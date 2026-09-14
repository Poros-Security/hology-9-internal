#!/usr/bin/env python3
import json
import os
import socket
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from threading import Lock
import socketserver

HOST = os.getenv("CTF_HOST", "0.0.0.0")
PORT = int(os.getenv("CTF_PORT", "2234"))

_timeout_env = os.getenv("CTF_TIMEOUT", "60").strip()
TIMEOUT = float(_timeout_env) if _timeout_env else None

RATE_LIMIT = int(os.getenv("CTF_RATE_LIMIT", "10"))
RATE_WINDOW = int(os.getenv("CTF_RATE_WINDOW", "60"))

BANNER = """\nWELCOME TO THE HackItBraw FORENSICS CHALLENGE!\n"""

QNA_PATH = Path(os.getenv("CTF_QNA_FILE", "qna.json"))


def _load_questions(path: Path):
    try:
        with path.open() as f:
            data = json.load(f)
    except FileNotFoundError:
        raise SystemExit(f"[!] QnA file not found: {path}")
    except json.JSONDecodeError as e:
        raise SystemExit(f"[!] Invalid JSON in {path}: {e}")

    if not isinstance(data, list) or not data:
        raise SystemExit(f"[!] {path} must be a non-empty JSON array")

    required = {"num": int, "question": str, "format": str, "answer": str}
    seen_nums = set()
    for i, q in enumerate(data):
        if not isinstance(q, dict):
            raise SystemExit(f"[!] {path}[{i}] must be an object")
        for key, typ in required.items():
            if key not in q:
                raise SystemExit(f"[!] {path}[{i}] missing key '{key}'")
            if not isinstance(q[key], typ):
                raise SystemExit(
                    f"[!] {path}[{i}].{key} must be {typ.__name__}, got {type(q[key]).__name__}"
                )
        if q["num"] in seen_nums:
            raise SystemExit(f"[!] {path}[{i}] duplicate num={q['num']}")
        seen_nums.add(q["num"])
    return data


QUESTIONS = _load_questions(QNA_PATH)


def _load_flag():
    for name in ("GZCTF_FLAG", "CTF_GZFLAG"):
        flag = os.getenv(name)
        if flag:
            if "[TEAM_HASH]" in flag:
                raise SystemExit(
                    f"[!] {name} still contains unresolved [TEAM_HASH]; "
                    "expected a generated team flag"
                )
            return flag
    raise SystemExit("[!] GZCTF_FLAG env var is required")


FLAG = _load_flag()


_state_lock = Lock()
_conn_window = {}     # ip -> deque[monotonic timestamps] for sliding window
_wrong_total = {}     # ip -> cumulative wrong-answer count (lifetime of process)
_rl_hits = {}         # ip -> cumulative rate-limit rejections


def _log(ip, event, **kwargs):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    extras = "".join(f" {k}={v}" for k, v in kwargs.items())
    print(f"[{ts}] [{ip}] {event}{extras}", flush=True)


def _allow_connection(ip):
    """Sliding-window rate limit. Returns (allowed, conn_count_in_window)."""
    now = time.monotonic()
    with _state_lock:
        dq = _conn_window.setdefault(ip, deque())
        while dq and now - dq[0] > RATE_WINDOW:
            dq.popleft()
        if len(dq) >= RATE_LIMIT:
            _rl_hits[ip] = _rl_hits.get(ip, 0) + 1
            return False, len(dq)
        dq.append(now)
        return True, len(dq)


class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        ip = self.client_address[0]

        allowed, in_window = _allow_connection(ip)
        if not allowed:
            with _state_lock:
                hits = _rl_hits.get(ip, 0)
            _log(ip, "RATE_LIMITED", in_window=in_window, hits=hits)
            try:
                self.request.sendall(
                    f"\n[!] Too many connections. Try again in {RATE_WINDOW}s.\n".encode()
                )
            except Exception:
                pass
            return

        if TIMEOUT is not None:
            self.request.settimeout(TIMEOUT)

        # Line-buffered reader so a single recv that contains multiple
        # client lines (e.g. a fast pwntools batch) gets split correctly
        # — one line per question, leftover bytes stay buffered.
        rfile = self.request.makefile("rb", buffering=4096)

        _log(ip, "CONNECT", in_window=in_window + 1)

        try:
            self.request.sendall(BANNER.encode())
        except Exception:
            _log(ip, "DISCONNECT", stage="banner")
            return

        total = len(QUESTIONS)
        for q in QUESTIONS:
            try:
                self.request.sendall(
                    f"---------------------------------------------------------\n"
                    f"  Question {q['num']}/{total}\n"
                    f"  {q['question']}\n"
                    f"  Format: {q['format']}\n"
                    f"---------------------------------------------------------\n"
                    f">>> Answer: ".encode()
                )
                data = rfile.readline(4096)
            except socket.timeout:
                _log(ip, "TIMEOUT", q=q["num"])
                try:
                    self.request.sendall(b"\n[!] Connection timed out.\n")
                except Exception:
                    pass
                return
            except Exception:
                _log(ip, "DISCONNECT", q=q["num"])
                return

            if not data:
                _log(ip, "DISCONNECT", q=q["num"], reason="eof")
                return

            try:
                answer = data.decode(errors="replace").strip()
            except Exception:
                _log(ip, "DISCONNECT", q=q["num"], reason="decode")
                return

            if answer.lower() == "exit":
                _log(ip, "EXIT", q=q["num"])
                try:
                    self.request.sendall(b"\n[!] Goodbye, investigator.\n")
                except Exception:
                    pass
                return

            if answer.lower() != q["answer"].lower():
                with _state_lock:
                    wrong = _wrong_total.get(ip, 0) + 1
                    _wrong_total[ip] = wrong
                _log(ip, "WRONG", q=q["num"], total_wrong=wrong)
                try:
                    self.request.sendall(b"[-] Wrong answer! Investigation failed.\n")
                except Exception:
                    pass
                return

            try:
                self.request.sendall(b"[+] Correct!\n\n")
            except Exception:
                _log(ip, "DISCONNECT", q=q["num"], reason="send_fail")
                return

        _log(ip, "SOLVED")
        try:
            self.request.sendall(f"\n  FLAG: {FLAG}\n\n".encode())
        except Exception:
            pass


class Server(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    with Server((HOST, PORT), Handler) as s:
        print(f"[*] Running on {HOST}:{PORT}", flush=True)
        print(f"[*] Rate limit: {RATE_LIMIT} conn / {RATE_WINDOW}s per IP", flush=True)
        if TIMEOUT is not None:
            print(f"[*] Connection idle timeout: {TIMEOUT}s", flush=True)
        else:
            print("[*] Connection idle timeout: disabled", flush=True)
        s.serve_forever()
