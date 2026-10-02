"""Tiny client for the isolated UNIX-socket flag service."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import socket


class FlagVault:
    def __init__(self, socket_path: str | None = None, auth_key: str | None = None):
        self._socket_path = socket_path or os.getenv("REWARD_SOCKET", "/tmp/pyjail_reward.sock")
        self._auth_key = (auth_key or os.getenv("REWARD_KEY", "")).encode()

    def _request(self, operation: str, session: str, stage: int = 0) -> str:
        body = f"{operation}|{session}|{stage}"
        signature = hmac.new(self._auth_key, body.encode(), hashlib.sha256).hexdigest()
        message = json.dumps({"op": operation, "session": session, "stage": stage, "auth": signature}) + "\n"
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
            conn.settimeout(2.0)
            conn.connect(self._socket_path)
            conn.sendall(message.encode())
            response = conn.makefile("r", encoding="utf-8").readline(2048)
        data = json.loads(response)
        if not data.get("ok"):
            return ""
        return str(data.get("value", ""))

    def record_stage(self, session: str, stage: int) -> bool:
        return self._request("mark", session, stage) == "accepted"

    def claim(self, session: str, completed: list[bool]) -> str | None:
        if completed != [True] * 5:
            return None
        value = self._request("claim", session, 5)
        return value or None
