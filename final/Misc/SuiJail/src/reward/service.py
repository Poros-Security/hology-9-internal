"""Reward daemon. The dynamic flag only exists in this process environment."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import socket
import stat
import threading


class RewardLedger:
    def __init__(self, flag: str, auth_key: str):
        self.flag = flag
        self.auth_key = auth_key.encode()
        self.sessions: dict[str, set[int]] = {}
        self.lock = threading.Lock()

    def handle(self, request: dict[str, object]) -> dict[str, object]:
        operation = str(request.get("op", ""))
        session = str(request.get("session", ""))
        stage = int(request.get("stage", 0))
        expected = hmac.new(
            self.auth_key,
            f"{operation}|{session}|{stage}".encode(),
            hashlib.sha256,
        ).hexdigest()
        supplied = str(request.get("auth", ""))
        if not session or not hmac.compare_digest(expected, supplied):
            return {"ok": False, "value": "denied"}
        with self.lock:
            progress = self.sessions.setdefault(session, set())
            if operation == "mark":
                if stage != len(progress) + 1 or stage not in range(1, 6):
                    return {"ok": False, "value": "out-of-order"}
                progress.add(stage)
                return {"ok": True, "value": "accepted"}
            if operation == "claim" and stage == 5 and progress == {1, 2, 3, 4, 5}:
                return {"ok": True, "value": self.flag}
        return {"ok": False, "value": "incomplete"}


def serve(path: str, flag: str, key: str) -> None:
    try:
        if stat.S_ISSOCK(os.stat(path).st_mode):
            os.unlink(path)
    except FileNotFoundError:
        pass
    ledger = RewardLedger(flag, key)
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(path)
    socket_mode = int(os.environ.get("REWARD_SOCKET_MODE", "0o600"), 8)
    os.chmod(path, socket_mode)
    server.listen(32)
    while True:
        conn, _ = server.accept()
        threading.Thread(target=client, args=(conn, ledger), daemon=True).start()


def client(conn: socket.socket, ledger: RewardLedger) -> None:
    with conn:
        conn.settimeout(2.0)
        try:
            raw = conn.makefile("rb").readline(2048)
            if not raw.endswith(b"\n"):
                response = {"ok": False, "value": "bad request"}
            else:
                request = json.loads(raw)
                response = ledger.handle(request)
        except (ValueError, OSError, TypeError):
            response = {"ok": False, "value": "bad request"}
        conn.sendall((json.dumps(response) + "\n").encode())


if __name__ == "__main__":
    serve(
        os.environ.get("REWARD_SOCKET", "/tmp/pyjail_reward.sock"),
        os.environ.get("GZCTF_FLAG", "FLAG{development_flag}"),
        os.environ.get("REWARD_KEY", "development-only-key"),
    )
