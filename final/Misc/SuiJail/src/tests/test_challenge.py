from __future__ import annotations

import multiprocessing
import os
import tempfile
import time
from io import StringIO

from engine.game import Game, checkpoint_for, checkpoint_level, checkpoint_state
from engine.colors import Palette, visible_width
from engine.renderer import Renderer
from reward.service import serve
from reward.vault import FlagVault
from security.evaluator import Evaluator
from security.policies import POLICIES


class MemoryVault:
    def __init__(self):
        self.records: dict[str, list[int]] = {}

    def record_stage(self, session: str, stage: int) -> bool:
        self.records.setdefault(session, []).append(stage)
        return True

    def claim(self, session: str, completed: list[bool]) -> str | None:
        if completed == [True] * 5 and self.records.get(session) == [1, 2, 3, 4, 5]:
            return "FLAG{test_reward}"
        return None


def submit(game: Game, source: str):
    result = Evaluator(POLICIES[game.stage_number]).evaluate(source, game.names())
    assert result.error is None, result.error
    game.after_evaluation()
    game.drain_events()
    return result.value


def walk_to_exit(game: Game):
    for _ in range(3):
        submit(game, 'player("south")')


def test_normal_movement_and_locked_door_collision():
    game = Game(vault=MemoryVault(), color=False)
    submit(game, 'getattr(getattr(player, "position"), "__setitem__")(0, 4)')
    submit(game, 'player("south")')
    assert game.player.position == [4, 3]
    message = submit(game, 'player("south")')
    assert message == "The locked gate refuses to move."
    assert game.player.position == [4, 3]


def test_guard_blocks_until_mutable_policy_is_cleared():
    game = Game(vault=MemoryVault(), start_stage=2, color=False)
    message = submit(game, 'player("south")')
    assert message == "The guard blocks the corridor."
    submit(game, 'getattr(getattr(getattr(getattr(player, "room"), "entities")[1], "protocol"), "clear")()')
    assert "blocking" not in game.stage.room.entities[1].protocol
    walk_to_exit(game)
    assert game.stage_number == 3


def test_jail1_mutable_prisoner_exploit():
    vault = MemoryVault()
    game = Game(vault=vault, session_id="j1", color=False)
    submit(game, "dir(player)")
    submit(game, 'getattr(getattr(player, "position"), "__setitem__")(0, 4)')
    result = Evaluator(POLICIES[1]).evaluate('getattr(getattr(player, "position"), "__setitem__")(1, 5)', game.names())
    assert result.error is None
    game.after_evaluation()
    events = game.drain_events()
    assert game.stage_number == 2
    assert vault.records["j1"] == [1]
    assert ("breach", "####D####  ->  ####@####") in events


def test_jail2_indirect_entity_graph_exploit():
    vault = MemoryVault()
    game = Game(vault=vault, session_id="j2", start_stage=2, color=False)
    submit(game, 'getattr(getattr(getattr(getattr(player, "room"), "entities")[1], "protocol"), "clear")()')
    walk_to_exit(game)
    assert game.stage_number == 3
    assert vault.records["j2"] == [2]


def test_jail3_bound_method_reaches_remote_actuator():
    vault = MemoryVault()
    game = Game(vault=vault, session_id="j3", start_stage=3, color=False)
    submit(game, "dir(player.warden)")
    value = submit(game, 'getattr(getattr(getattr(getattr(getattr(getattr(player, "warden"), "__self__"), "world"), "rooms")[1], "doors")[0], "unlock")()')
    assert "distant lock" in value
    assert not game.current_door().locked
    walk_to_exit(game)
    assert game.stage_number == 4
    assert vault.records["j3"] == [3]


def test_jail4_hardened_ast_keeps_callable_closure_capability():
    vault = MemoryVault()
    game = Game(vault=vault, session_id="j4", start_stage=4, color=False)
    evaluator = Evaluator(POLICIES[4])
    rejected = evaluator.evaluate("player.panel._callback('camera_grid')", game.names())
    assert rejected.code == "JAIL-451"
    assert submit(game, "dir(player)")
    assert "camera_grid" in submit(game, "repr(player)")
    value = submit(game, "player('camera_grid')")
    assert "CAMERA GRID OFFLINE" in value
    assert all(not entity.active for entity in game.stage.room.entities if hasattr(entity, "active"))
    assert not game.current_door().locked
    walk_to_exit(game)
    assert game.stage_number == 5
    assert vault.records["j4"] == [4]


def test_jail5_manager_completion_releases_flag():
    vault = MemoryVault()
    vault.records["j5"] = [1, 2, 3, 4]
    game = Game(vault=vault, session_id="j5", start_stage=5, completed=[True] * 4 + [False], color=False)
    submit(game, "dir(player.warden.__self__)")
    submit(game, 'getattr(getattr(getattr(getattr(getattr(player, "warden"), "__self__"), "manager"), "completed"), "__setitem__")(4, True)')
    value = submit(game, 'getattr(getattr(getattr(getattr(player, "warden"), "__self__"), "manager"), "check_completion")()')
    assert "PRISONER STATUS: FREE" in value
    assert "FLAG{test_reward}" in value
    assert game.escaped
    assert vault.records["j5"] == [1, 2, 3, 4, 5]


def test_checkpoint_signing_and_restore_state():
    secret = b"checkpoint-test-key"
    token = checkpoint_for(3, secret, "session-abc")
    assert checkpoint_level(token, secret) == 3
    assert checkpoint_state(token, secret) == (3, "session-abc")
    assert checkpoint_state(token + "x", secret) is None
    assert checkpoint_state("PYJAIL-99-session-bad-nope", secret) is None
    restored = Game(vault=MemoryVault(), session_id="session-abc", completed=[True] * 3 + [False, False], start_stage=4, color=False)
    assert restored.stage_number == 4
    assert restored._manager.completed == [True, True, True, False, False]


def test_ast_policy_rejects_assignment_attributes_and_unknown_dunders():
    evaluator = Evaluator(POLICIES[1])
    assignment = evaluator.evaluate("player.position = [1, 2]", {"player": object()})
    assert assignment.code == "PY-SYNTAX"
    blocked = evaluator.evaluate("player.__class__", {"player": object()})
    assert blocked.code == "JAIL-451"
    hardened = Evaluator(POLICIES[4]).evaluate("player.position", {"player": object()})
    assert hardened.code == "JAIL-451"
    assert Evaluator(POLICIES[1]).evaluate("getattr(player, 'position')", {"player": object()}).error.startswith("AttributeError")
    assert Evaluator(POLICIES[1]).evaluate("getattr(player, '__class__')", {"player": object()}).code == "JAIL-451"


def test_python_builtins_replace_custom_shell_helpers():
    game = Game(vault=MemoryVault(), color=False)
    evaluator = Evaluator(POLICIES[1])
    assert "position" in evaluator.evaluate("dir(player)", game.names()).value
    assert evaluator.evaluate("repr(player)", game.names()).value.startswith("<Player")
    assert set(game.names()) == {"player"}
    for helper in ("look", "inspect", "move", "interact", "help"):
        assert evaluator.evaluate(helper, game.names()).code == "PY-RUNTIME"
    assert evaluator.evaluate('getattr(player, "position")', game.names()).value is game.player.position
    assert evaluator.evaluate('getattr(player, "world")', game.names()).code == "JAIL-451"
    assert evaluator.evaluate("map", game.names()).code == "PY-RUNTIME"
    assert evaluator.evaluate('getattr(player, name)', {"player": game.player, "name": "world"}).code == "JAIL-451"


def test_flag_name_is_not_in_the_early_shell_namespace():
    game = Game(vault=MemoryVault(), color=False)
    result = Evaluator(POLICIES[1]).evaluate("FLAG", game.names())
    assert result.code == "PY-RUNTIME"
    assert "FLAG" not in game.names()


def test_input_and_output_limits_and_frame_width():
    evaluator = Evaluator(POLICIES[1])
    assert evaluator.evaluate(" " * 241, {}).code == "JAIL-413"
    rendered = evaluator.format_value("x" * 1400)
    assert len(rendered) <= 1200 + len("... <output truncated>")
    stream = StringIO()
    Renderer(Palette(False)).draw(Game(vault=MemoryVault(), color=False), stream)
    output = stream.getvalue()
    assert "PENITENTIARY" in output
    assert "PYTHON PENITENTIARY" not in output
    framed = [line for line in output.splitlines() if line.startswith("║") or line.startswith("╔") or line.startswith("╚")]
    assert framed and all(len(line) >= Renderer.WIDTH and line[Renderer.WIDTH - 1] in "║╗╣╝" for line in framed)
    assert max(map(len, output.splitlines())) <= 80
    legend_line = next(line for line in framed if "TILES" in line)
    assert legend_line[Renderer.WIDTH - 1] == "║"
    assert "  TILES" in legend_line[Renderer.WIDTH:]
    for legend_entry in ("@ player", "# wall", ". floor", "D locked", "/ open", "G guard", "g disabled", "K key", "T term", "C camera", "c disabled", "! alarm"):
        assert legend_entry in output
    assert output.count("We couldn't move the bars. So we moved ourselves.") == 1
    assert "PY BUILTINS" not in output
    assert "\x1b[" not in output
    assert max(visible_width(line) for line in output.splitlines()) <= 80
    for stage in range(2, 6):
        stage_stream = StringIO()
        staged = Game(vault=MemoryVault(), start_stage=stage, color=False)
        Renderer(Palette(False)).draw(staged, stage_stream)
        assert max(visible_width(line) for line in stage_stream.getvalue().splitlines()) <= 80


def test_evaluation_timeout_interrupts_slow_callable():
    evaluator = Evaluator(POLICIES[1])
    evaluator.policy = type(POLICIES[1])("test", POLICIES[1].nodes, POLICIES[1].attributes, timeout=0.02)
    started = time.monotonic()
    result = evaluator.evaluate("stall()", {"stall": lambda: time.sleep(1)})
    assert result.code == "JAIL-500"
    assert time.monotonic() - started < 0.5


def test_flag_service_holds_reward_until_signed_full_progress():
    with tempfile.TemporaryDirectory() as temp:
        path = os.path.join(temp, "reward.sock")
        key = "integration-secret"
        process = multiprocessing.Process(target=serve, args=(path, "FLAG{isolated}", key), daemon=True)
        process.start()
        try:
            deadline = time.monotonic() + 3
            while not os.path.exists(path) and time.monotonic() < deadline:
                time.sleep(0.01)
            vault = FlagVault(path, key)
            assert vault.claim("session", [True] * 5) is None
            for stage in range(1, 5):
                assert vault.record_stage("session", stage)
            assert vault.claim("session", [True] * 5) is None
            assert vault.record_stage("session", 5)
            assert vault.claim("session", [True] * 5) == "FLAG{isolated}"
        finally:
            process.terminate()
            process.join(timeout=2)


def test_sessions_have_independent_world_state():
    first = Game(vault=MemoryVault(), color=False)
    second = Game(vault=MemoryVault(), color=False)
    submit(first, 'getattr(getattr(player, "position"), "__setitem__")(0, 0)')
    assert first.player.position == [0, 2]
    assert second.player.position == [3, 2]
