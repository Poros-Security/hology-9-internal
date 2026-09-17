import base64
import hashlib
import hmac
import json


def encode(raw):
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode(value):
    if not value or len(value) > 1536:
        raise ValueError("Invalid ticket size.")
    return base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)


def canonical(claims):
    return json.dumps(claims, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode()


def first_members(pairs):
    result = {}
    for name, value in pairs:
        result.setdefault(name, value)
    return result


def unique_members(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("Ambiguous ticket object.")
        result[name] = value
    return result


def sign(claims, key):
    raw = canonical(claims)
    return encode(raw) + "." + hmac.new(key, raw, hashlib.sha256).hexdigest()


def verify(token, key, *, strict=False):
    body, signature = token.split(".")
    raw = decode(body)
    claims = json.loads(raw, object_pairs_hook=unique_members if strict else first_members)
    if not isinstance(claims, dict) or any(type(v) not in (str, int) for v in claims.values()):
        raise ValueError("Ticket claims must be a flat object of strings and integers.")
    expected = hmac.new(key, canonical(claims), hashlib.sha256).hexdigest()
    if not signature.isascii() or not hmac.compare_digest(expected, signature):
        raise ValueError("Ticket integrity check failed.")
    # The migrated consumer uses its native object decoder after legacy verification.
    consumed = claims if strict else json.loads(raw)
    if any(type(v) not in (str, int) for v in consumed.values()):
        raise ValueError("Ticket claims must be scalar.")
    return consumed
