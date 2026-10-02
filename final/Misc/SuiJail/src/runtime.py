"""Starts the private reward daemon and keeps its key out of the server environment."""

from __future__ import annotations

import os
import secrets
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def start_reward_service() -> tuple[subprocess.Popen, str, str]:
    flag = os.environ.pop("GZCTF_FLAG", None) or os.environ.pop("FLAG", None) or "FLAG{development_flag}"
    auth_key = secrets.token_hex(32)
    socket_path = str(Path(tempfile.gettempdir()) / f"pyjail-reward-{os.getpid()}-{secrets.token_hex(4)}.sock")
    child_env = {
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        "PYTHONPATH": str(ROOT),
        "PYTHONUNBUFFERED": "1",
        "REWARD_SOCKET": socket_path,
        "REWARD_KEY": auth_key,
        "GZCTF_FLAG": flag,
    }
    process = subprocess.Popen(
        [sys.executable, "-m", "reward.service"],
        cwd=ROOT,
        env=child_env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("reward service exited during startup")
        if os.path.exists(socket_path):
            return process, socket_path, auth_key
        time.sleep(0.025)
    process.terminate()
    raise RuntimeError("reward service did not create its private socket")


def stop_reward_service(process: subprocess.Popen, socket_path: str) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2.0)
    try:
        os.unlink(socket_path)
    except FileNotFoundError:
        pass
