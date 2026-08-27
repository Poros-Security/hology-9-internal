"""Metadata-only obfuscation for the Ouroboros stage-1 code object.

Everything in here is deliberately restricted to fields that do *not* live in
`co_code`. The decryption key is the FNV-1a hash of `_boot.__code__.co_code`,
so a single changed instruction byte would brick the challenge; gen.py asserts
that `co_code` is byte-identical before and after this pass.
"""

import itertools
import types

FAKE_FILENAME = "<frozen importlib._bootstrap>"
FAKE_LINENO = 1337

_FIRST = "lI"
_REST = "lI1"


def confusables(count):
    """`l`, `I`, `ll`, `lI`, `l1`, `Il`, ... -- valid, unique, unreadable."""
    out = []
    width = 1
    while len(out) < count:
        for combo in itertools.product(_FIRST, *([_REST] * (width - 1))):
            out.append("".join(combo))
            if len(out) >= count:
                break
        width += 1
    return tuple(out[:count])


def scrub(code, drop_doc=False, blank_lines=True):
    """Rewrite metadata recursively. Never touches co_code or co_names."""
    consts = []
    for index, const in enumerate(code.co_consts):
        if isinstance(const, types.CodeType):
            consts.append(scrub(const, drop_doc=False, blank_lines=blank_lines))
        elif drop_doc and index == 0 and isinstance(const, str):
            consts.append(None)          # blank the docstring
        else:
            consts.append(const)

    fields = {
        "co_consts": tuple(consts),
        "co_varnames": confusables(len(code.co_varnames)),
        "co_filename": FAKE_FILENAME,
        "co_firstlineno": FAKE_LINENO,
    }
    if blank_lines:
        fields["co_linetable"] = b""     # tracebacks and decompilers get nothing
    return code.replace(**fields)


def code_map(code, out=None, path="<module>"):
    """name -> co_code, for the before/after equality assertion."""
    if out is None:
        out = {}
    out[path] = code.co_code
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            code_map(const, out, "%s.%s" % (path, const.co_name))
    return out
