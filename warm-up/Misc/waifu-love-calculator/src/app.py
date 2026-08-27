import json
import os
import re
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs

from ml_model import ensure_model

BASE_DIR = Path(__file__).resolve().parent
INITIAL_RE = re.compile(r"^[A-Za-z]{2}$")

FLAG = os.environ.get("GZCTF_FLAG") or os.environ.get("FLAG") or "HOLOGY9{flag_not_configured}"
SECRET_A = os.environ.get("SECRET_A", "WA").upper()
SECRET_B = os.environ.get("SECRET_B", "FU").upper()
MODEL_PATH = Path(os.environ.get("MODEL_PATH", str(BASE_DIR / "model" / "waifu_model.npz")))


def sanitize_secret(value: str, fallback: str) -> str:
    value = (value or "").strip().upper()
    if not re.fullmatch(r"[A-Z]{2}", value):
        return fallback
    return value


SECRET_A = sanitize_secret(SECRET_A, "WA")
SECRET_B = sanitize_secret(SECRET_B, "FU")
TARGET = SECRET_A + SECRET_B
MODEL = ensure_model(MODEL_PATH, TARGET)


def calculate(a: str, b: str) -> dict:
    a = a.upper()
    b = b.upper()
    exact = a == SECRET_A and b == SECRET_B

    logit = MODEL.logit(a, b)
    confidence = MODEL.probability(a, b)

    compatibility = 100.0 if exact else min(99.0, confidence * 100.0)
    return {
        "person_a": a,
        "person_b": b,
        "compatibility": round(compatibility, 6),
        "rounded_percent": int(round(compatibility)),
        "match": exact,
        "flag": FLAG if exact else None,
        "model_name": MODEL.metadata.get("model_version", "unknown"),
        "model_features": MODEL.metadata.get("features", "unknown"),
        "model_confidence": f"{confidence:.12f}",
        "model_logit": f"{logit:.12f}",
    }


def read_body(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length", "0") or "0")
    raw = handler.rfile.read(length) if length else b""
    content_type = handler.headers.get("Content-Type", "")
    if "application/json" in content_type:
        try:
            return json.loads(raw.decode("utf-8")) if raw else {}
        except json.JSONDecodeError:
            return {}
    if "application/x-www-form-urlencoded" in content_type:
        parsed = parse_qs(raw.decode("utf-8"))
        return {k: v[-1] for k, v in parsed.items()}
    return {}


class WaifuHandler(BaseHTTPRequestHandler):
    server_version = "WaifuLoveCalculator/2.0"

    def send_bytes(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_bytes(status, body, "application/json; charset=utf-8")

    def do_GET(self) -> None:
        if self.path == "/" or self.path.startswith("/?"):
            body = (BASE_DIR / "templates" / "index.html").read_bytes()
            self.send_bytes(200, body, "text/html; charset=utf-8")
            return
        if self.path == "/static/style.css":
            body = (BASE_DIR / "static" / "style.css").read_bytes()
            self.send_bytes(200, body, "text/css; charset=utf-8")
            return
        if self.path == "/healthz":
            self.send_bytes(200, b"ok", "text/plain; charset=utf-8")
            return
        self.send_json(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path != "/api/calculate":
            self.send_json(404, {"error": "not found"})
            return
        data = read_body(self)
        a = str(data.get("person_a") or data.get("a") or "").strip()
        b = str(data.get("person_b") or data.get("b") or "").strip()
        if not INITIAL_RE.fullmatch(a) or not INITIAL_RE.fullmatch(b):
            self.send_json(
                400,
                {
                    "error": "Each person's initials must be exactly two letters, A-Z.",
                    "example": {"person_a": "AB", "person_b": "CD"},
                },
            )
            return
        self.send_json(200, calculate(a, b))

    def log_message(self, fmt: str, *args) -> None:
        if os.environ.get("DEBUG"):
            super().log_message(fmt, *args)


def main() -> None:
    port = int(os.environ.get("PORT", "5000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), WaifuHandler)
    print(f"Waifu Love Calculator listening on http://0.0.0.0:{port}")
    print(f"Loaded ML model: {MODEL.metadata.get('model_version')} from {MODEL_PATH}")
    server.serve_forever()


if __name__ == "__main__":
    main()
