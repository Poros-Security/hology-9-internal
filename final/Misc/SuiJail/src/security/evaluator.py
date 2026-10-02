"""Expression-only evaluator with an interrupting timeout and bounded output."""

from __future__ import annotations

import ast
import builtins
import signal
import sys
from dataclasses import dataclass
from typing import Any

from .policies import Policy, PolicyViolation, validate


SAFE_BUILTINS = {
    name: getattr(builtins, name)
    for name in (
        "abs",
        "all",
        "any",
        "bool",
        "dict",
        "dir",
        "enumerate",
        "float",
        "getattr",
        "hasattr",
        "int",
        "isinstance",
        "iter",
        "len",
        "list",
        "max",
        "min",
        "next",
        "repr",
        "reversed",
        "round",
        "set",
        "sorted",
        "str",
        "sum",
        "tuple",
        "type",
        "zip",
    )
}


class EvalTimeout(TimeoutError):
    pass


def _timeout_handler(_signum: int, _frame: Any) -> None:
    raise EvalTimeout("evaluation exceeded its time budget")


@dataclass
class EvalResult:
    value: Any = None
    error: str | None = None
    code: str = ""


class Evaluator:
    def __init__(self, policy: Policy, output_limit: int = 1200):
        self.policy = policy
        self.output_limit = output_limit

    def evaluate(self, source: str, names: dict[str, Any]) -> EvalResult:
        if len(source) > self.policy.max_length:
            return EvalResult(error=f"input exceeds {self.policy.max_length} characters", code="JAIL-413")
        try:
            tree = ast.parse(source, mode="eval")
            validate(tree, self.policy)
            signal.signal(signal.SIGALRM, _timeout_handler)
            signal.setitimer(signal.ITIMER_REAL, self.policy.timeout)
            try:
                globals_dict = {"__builtins__": SAFE_BUILTINS}
                value = eval(compile(tree, "<jail>", "eval"), globals_dict, names)
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
            return EvalResult(value=value)
        except PolicyViolation as exc:
            return EvalResult(error=str(exc)[: self.output_limit], code="JAIL-451")
        except EvalTimeout as exc:
            return EvalResult(error=str(exc)[: self.output_limit], code="JAIL-500")
        except SyntaxError as exc:
            detail = exc.msg
            if exc.offset:
                detail += f" (column {exc.offset})"
            return EvalResult(error=detail[: self.output_limit], code="PY-SYNTAX")
        except BaseException as exc:
            return EvalResult(error=f"{type(exc).__name__}: {exc}"[: self.output_limit], code="PY-RUNTIME")
        finally:
            try:
                sys.setrecursionlimit(900)
            except RecursionError:
                pass

    def format_value(self, value: Any) -> str:
        try:
            rendered = repr(value)
        except BaseException as exc:
            rendered = f"<{type(value).__name__} repr raised {type(exc).__name__}>"
        if len(rendered) > self.output_limit:
            return rendered[: self.output_limit] + "... <output truncated>"
        return rendered
