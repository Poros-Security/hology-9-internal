"""Process-per-connection TCP server for GZCTF DynamicContainer."""

from __future__ import annotations

import multiprocessing
import os
import signal
import socket

from engine.console import play
from reward.vault import FlagVault
from runtime import start_reward_service, stop_reward_service


HOST = "0.0.0.0"
PORT = 31337
MAX_CLIENTS = 8


def _client_worker(connection: socket.socket, socket_path: str, key: str) -> None:
    try:
        connection.settimeout(300)
        reader = connection.makefile("r", encoding="utf-8", newline="\n")
        writer = connection.makefile("w", encoding="utf-8", newline="\n", buffering=1)
        play(reader, writer, vault=FlagVault(socket_path, key))
    except (BrokenPipeError, ConnectionResetError, OSError):
        pass
    finally:
        try:
            connection.close()
        except OSError:
            pass


def run_server(host: str = HOST, port: int = PORT) -> None:
    reward_process = None
    if os.getenv("REWARD_EXTERNAL") == "1":
        socket_path = os.environ["REWARD_SOCKET"]
        key_fd = int(os.environ.pop("REWARD_KEY_FD"))
        key = os.read(key_fd, 128).decode()
        os.close(key_fd)
        os.environ.pop("REWARD_KEY", None)
    else:
        reward_process, socket_path, key = start_reward_service()
    context = multiprocessing.get_context("fork")
    children: list[multiprocessing.Process] = []
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        listener.bind((host, port))
        listener.listen(64)
        listener.settimeout(1.0)
        print(f"Prison listening on {host}:{port}", flush=True)
        while True:
            children = [child for child in children if child.is_alive()]
            try:
                connection, _address = listener.accept()
            except socket.timeout:
                continue
            if len(children) >= MAX_CLIENTS:
                connection.sendall(b"[WARDEN] All cells are occupied. Reconnect shortly.\n")
                connection.close()
                continue
            child = context.Process(target=_client_worker, args=(connection, socket_path, key), daemon=True)
            child.start()
            connection.close()
            children.append(child)
    except KeyboardInterrupt:
        pass
    finally:
        listener.close()
        for child in children:
            if child.is_alive():
                child.terminate()
            child.join(timeout=1.0)
        if reward_process is not None:
            stop_reward_service(reward_process, socket_path)


if __name__ == "__main__":
    run_server()
