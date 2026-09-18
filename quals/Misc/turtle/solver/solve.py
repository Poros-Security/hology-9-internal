#!/usr/bin/env python3

import argparse
import socket
import sys
import time


ANSWERS = [
    "-8.324, 112.203",
    "Serang",
    "Dwi Handoko",
    "Dikasih Kopi",
    "Dita Faisal",
    "Forum Pemuda Peduli Serang",
]


def recv_until_prompt(sock, timeout=5):
    sock.settimeout(timeout)
    data = b""

    while True:
        try:
            chunk = sock.recv(4096)
        except socket.timeout:
            break

        if not chunk:
            break

        data += chunk

        # chall.py menggunakan "> " sebagai prompt
        if b"> " in data:
            break

    return data


def solve(host, port):
    print(f"[*] Connecting to {host}:{port}")

    try:
        sock = socket.create_connection((host, port), timeout=5)
    except OSError as e:
        print(f"[-] Connection failed: {e}")
        sys.exit(1)

    with sock:
        print("[+] Connected")

        for i, answer in enumerate(ANSWERS, 1):
            output = recv_until_prompt(sock)

            if output:
                print(output.decode(errors="replace"), end="")

            print(f"[>] Answer {i}: {answer}")

            sock.sendall((answer + "\n").encode())

            # Biar output server kebaca dengan nyaman
            time.sleep(0.1)

        # Baca hasil akhir / flag
        try:
            sock.settimeout(3)
            while True:
                data = sock.recv(4096)

                if not data:
                    break

                print(data.decode(errors="replace"), end="")

        except socket.timeout:
            pass

    print("\n[+] Connection closed")


def main():
    parser = argparse.ArgumentParser(
        description="Solver for turtle OSINT CTF challenge"
    )

    parser.add_argument(
        "host",
        help="Target IP / hostname"
    )

    parser.add_argument(
        "port",
        type=int,
        help="Target TCP port"
    )

    args = parser.parse_args()

    solve(args.host, args.port)


if __name__ == "__main__":
    main()
