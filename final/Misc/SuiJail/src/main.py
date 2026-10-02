"""Run one local interactive prison session."""

from __future__ import annotations

import sys

from engine.console import play
from reward.vault import FlagVault
from runtime import start_reward_service, stop_reward_service


def main() -> None:
    process, socket_path, key = start_reward_service()
    try:
        play(sys.stdin, sys.stdout, vault=FlagVault(socket_path, key))
    finally:
        stop_reward_service(process, socket_path)


if __name__ == "__main__":
    main()
