"""Per-stage AST grammars for the expression console."""

from __future__ import annotations

import ast
from dataclasses import dataclass


COMMON = {
    ast.Expression,
    ast.Constant,
    ast.Name,
    ast.Load,
    ast.Call,
    ast.keyword,
    ast.Tuple,
    ast.List,
    ast.Dict,
    ast.Set,
    ast.UnaryOp,
    ast.UAdd,
    ast.USub,
    ast.Not,
    ast.BoolOp,
    ast.And,
    ast.Or,
    ast.Compare,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.Is,
    ast.IsNot,
    ast.In,
    ast.NotIn,
}

NORMAL_NODES = COMMON | {ast.Attribute, ast.Subscript, ast.Slice}
HARDENED_NODES = COMMON


@dataclass(frozen=True)
class Policy:
    name: str
    nodes: frozenset[type[ast.AST]]
    attributes: frozenset[str]
    max_length: int = 240
    timeout: float = 0.35
    max_nodes: int = 80


POLICIES = {
    1: Policy("legacy", frozenset(NORMAL_NODES), frozenset({"position", "__setitem__", "room", "name", "hint", "move", "step", "locked", "x", "y", "entities", "doors", "exit", "rows", "tile_at", "protocol", "blocking", "text", "active", "__repr__"})),
    2: Policy("behavioral", frozenset(NORMAL_NODES), frozenset({"position", "room", "name", "hint", "move", "step", "locked", "x", "y", "entities", "doors", "exit", "rows", "tile_at", "protocol", "blocking", "text", "active", "clear", "add", "discard", "remove", "__len__", "__getitem__", "__repr__"})),
    3: Policy("warden-api", frozenset(NORMAL_NODES), frozenset({"__self__", "warden", "world", "rooms", "doors", "unlock", "name", "locked", "entities", "position", "room", "move", "step", "look", "__repr__"})),
    4: Policy("hardened", frozenset(HARDENED_NODES), frozenset()),
    5: Policy("panopticon", frozenset(NORMAL_NODES), frozenset({"__self__", "warden", "manager", "completed", "check_completion", "status", "__setitem__", "__getitem__", "move", "step", "world", "rooms", "name", "position", "room", "unlock", "doors", "locked", "__repr__"})),
}


class PolicyViolation(ValueError):
    pass


def validate(tree: ast.AST, policy: Policy) -> None:
    nodes = list(ast.walk(tree))
    if len(nodes) > policy.max_nodes:
        raise PolicyViolation("expression contains too many syntax nodes")
    for node in nodes:
        if type(node) not in policy.nodes:
            raise PolicyViolation(f"{type(node).__name__} syntax is unavailable in the {policy.name} interpreter")
        if isinstance(node, ast.Attribute) and node.attr not in policy.attributes:
            raise PolicyViolation(f"attribute {node.attr!r} is restricted")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "getattr":
            if len(node.args) < 2 or not isinstance(node.args[1], ast.Constant) or not isinstance(node.args[1].value, str):
                raise PolicyViolation("getattr requires a literal, stage-approved attribute name")
            if node.args[1].value not in policy.attributes:
                raise PolicyViolation(f"attribute {node.args[1].value!r} is restricted")
        if isinstance(node, ast.Name) and node.id.startswith("__"):
            raise PolicyViolation(f"name {node.id!r} is restricted")
        if isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes)) and len(node.value) > 96:
            raise PolicyViolation("string constants are limited to 96 characters")
        if isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool) and abs(node.value) > 10000:
            raise PolicyViolation("integer constants are limited to 10000 in magnitude")
