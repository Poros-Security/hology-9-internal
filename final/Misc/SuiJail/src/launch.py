"""Root startup shim that drops the game and vault into separate UIDs."""

from __future__ import annotations

import os
import secrets
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CHALLENGE_UID = 10001
VAULT_UID = 10002
CHALLENGE_GID = 10001


def drop_to(uid: int):
    def apply() -> None:
        os.setgroups([CHALLENGE_GID])
        os.setgid(CHALLENGE_GID)
        os.setuid(uid)

    return apply


def wait_for_socket(path: str, process: subprocess.Popen) -> None:
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("reward service exited during startup")
        if os.path.exists(path):
            return
        time.sleep(0.025)
    raise RuntimeError("reward service did not create its private socket")


def main() -> None:
    if os.geteuid() != 0:
        raise SystemExit("container launcher requires its limited setuid/setgid capabilities")
    flag = os.environ.pop("GZCTF_FLAG", None) or os.environ.pop("FLAG", None) or "FLAG{development_flag}"
    auth_key = secrets.token_hex(32)
    socket_path = str(Path(tempfile.gettempdir()) / f"pyjail-reward-{os.getpid()}-{secrets.token_hex(4)}.sock")
    reward_env = {
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        "PYTHONPATH": str(ROOT),
        "PYTHONUNBUFFERED": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "REWARD_SOCKET": socket_path,
        "REWARD_SOCKET_MODE": "0o660",
        "REWARD_KEY": auth_key,
        "GZCTF_FLAG": flag,
    }
    reward = subprocess.Popen(
        [sys.executable, "-m", "reward.service"],
        cwd=ROOT,
        env=reward_env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=drop_to(VAULT_UID),
    )
    del reward_env["GZCTF_FLAG"]
    del reward_env["REWARD_KEY"]
    del flag
    read_fd, write_fd = os.pipe()
    server_env = {
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        "PYTHONPATH": str(ROOT),
        "PYTHONUNBUFFERED": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "TERM": os.environ.get("TERM", "xterm-256color"),
        "REWARD_EXTERNAL": "1",
        "REWARD_SOCKET": socket_path,
        "REWARD_KEY_FD": str(read_fd),
    }
    if os.getenv("NO_COLOR"):
        server_env["NO_COLOR"] = os.environ["NO_COLOR"]
    elif os.environ.get("TERM") == "dumb":
        server_env["TERM"] = "dumb"
    else:
        server_env["FORCE_COLOR"] = os.environ.get("FORCE_COLOR", "1")

    def stop(_signum, _frame) -> None:
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    server = None
    try:
        wait_for_socket(socket_path, reward)
        server = subprocess.Popen(
            [sys.executable, "server.py"],
            cwd=ROOT,
            env=server_env,
            stdin=subprocess.DEVNULL,
            preexec_fn=drop_to(CHALLENGE_UID),
            pass_fds=(read_fd,),
        )
        os.close(read_fd)
        read_fd = -1
        os.write(write_fd, auth_key.encode())
        os.close(write_fd)
        write_fd = -1
        del auth_key
        server.wait()
    finally:
        for fd in (read_fd, write_fd):
            if fd >= 0:
                os.close(fd)
        if server is not None and server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=2)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=2)
        if reward.poll() is None:
            reward.terminate()
            try:
                reward.wait(timeout=2)
            except subprocess.TimeoutExpired:
                reward.kill()
                reward.wait(timeout=2)
        try:
            os.unlink(socket_path)
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    main()
