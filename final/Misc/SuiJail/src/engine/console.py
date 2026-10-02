"""Per-session prompt and evaluator loop."""

from __future__ import annotations

import resource
import socket
import sys
import time
from typing import TextIO

from engine.colors import Color
from engine.game import Game, checkpoint_state
from engine.renderer import Renderer
from security.evaluator import Evaluator
from security.policies import POLICIES


MAX_LINES = 700
MAX_LINE_LENGTH = 512
IDLE_TIMEOUT = 300


def _write(stream: TextIO, text: str) -> None:
    stream.write(text)
    if not text.endswith("\n"):
        stream.write("\n")
    stream.flush()


def _readline(reader: TextIO, writer: TextIO) -> str | None:
    try:
        raw = reader.readline(MAX_LINE_LENGTH + 2)
    except (TimeoutError, socket.timeout):
        _write(writer, "[WARDEN] Idle timeout. The cell door closes behind this session.")
        return None
    if raw == "":
        return None
    if len(raw) > MAX_LINE_LENGTH or not raw.endswith("\n"):
        _write(writer, "[JAIL-413] Input line is too long or incomplete.")
        return None
    return raw.rstrip("\r\n")


def _limits() -> None:
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (90, 95))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        resource.setrlimit(resource.RLIMIT_NOFILE, (48, 48))
    except (ValueError, OSError):
        pass
    sys.setrecursionlimit(900)


def play(reader: TextIO, writer: TextIO, game: Game | None = None, vault=None) -> Game | None:
    _limits()
    messages: list[tuple[str, str]] = []
    writer.write("\nPENITENTIARY\n")
    writer.write("Enter a signed checkpoint token to resume, or press return for a new sentence.\n")
    writer.write("Checkpoint: ")
    writer.flush()
    token = _readline(reader, writer)
    if token is None:
        return None
    if game is None:
        state = checkpoint_state(token) if token.strip() else None
        if token.strip() and state is None:
            messages.append(("error", "[JAIL-403] Checkpoint signature rejected. A fresh cell assignment follows."))
        elif state:
            messages.append(("system", "Checkpoint accepted. Restoring after CELL {}.".format(state[0])))
        completed = [bool(state and index < state[0]) for index in range(5)]
        game = Game(vault=vault, session_id=state[1] if state else None, completed=completed, start_stage=min(state[0] + 1, 5) if state else 1)
        if state and state[0] == 5:
            final_text = game.manager.check_completion()
            messages.extend(("result", line) for line in final_text.splitlines())
            for index, line in enumerate(messages):
                if line[1].startswith("FLAG{"):
                    messages[index] = ("flag", line[1])
                elif "ESCAPED" in line[1] or line[1] == "PRISONER STATUS: FREE":
                    messages[index] = ("success", line[1])
                elif line[1] == "SYSTEM INTEGRITY FAILURE":
                    messages[index] = ("error", line[1])
                elif line[1] == "MASTER LOCK RELEASED":
                    messages[index] = ("warning", line[1])
    renderer = Renderer(game.palette)
    evaluator = Evaluator(POLICIES[game.stage_number])
    renderer.draw(game, writer, messages)
    line_count = 0
    recent: list[float] = []
    while not game.escaped:
        source = _readline(reader, writer)
        if source is None:
            return game
        if source == ":quit":
            _write(writer, "[SYSTEM] Sentence suspended. Use the latest checkpoint when reconnecting.")
            return game
        if not source.strip():
            writer.write(Color.BOLD + Color.BRIGHT_CYAN + "py> " + Color.RESET if game.palette.enabled else "py> ")
            writer.flush()
            continue
        line_count += 1
        now = time.monotonic()
        recent = [stamp for stamp in recent if now - stamp < 2.0]
        recent.append(now)
        if line_count > MAX_LINES or len(recent) > 50:
            _write(writer, "[JAIL-429] Expression quota exhausted. The session is terminated.")
            return game
        policy = POLICIES[game.stage_number]
        if evaluator.policy is not policy:
            evaluator = Evaluator(policy)
        result = evaluator.evaluate(source, game.names())
        messages = []
        if result.error:
            code_color = Color.BRIGHT_RED if game.palette.enabled else ""
            reset = Color.RESET if game.palette.enabled else ""
            messages.append(("error", f"{code_color}[{result.code}]{reset} {result.error}"))
        elif result.value is not None:
            if isinstance(result.value, str):
                output = result.value[: evaluator.output_limit]
                for line in output.splitlines() or [""]:
                    if line == "SYSTEM INTEGRITY FAILURE":
                        kind = "error"
                    elif line == "MASTER LOCK RELEASED":
                        kind = "warning"
                    elif line.startswith("FLAG{"):
                        kind = "flag"
                    elif "ESCAPED" in line or line == "PRISONER STATUS: FREE" or line == "KEY FRAGMENT ε ACQUIRED":
                        kind = "success"
                    else:
                        kind = "result"
                    messages.append((kind, line))
            else:
                output = evaluator.format_value(result.value)
                messages.append(("result", output))
        try:
            game.after_evaluation()
            messages.extend(game.drain_events())
        except BaseException as exc:
            messages.append(("error", f"[JAIL-500] {type(exc).__name__}: {exc}"))
        renderer.draw(game, writer, messages)
        if game.escaped:
            break
        writer.flush()
    return game


def play_stdio() -> None:
    play(sys.stdin, sys.stdout)
