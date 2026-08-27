from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import random
import secrets
import struct
import threading
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


FLAG = os.environ.get("GZCTF_FLAG") or os.environ.get("FLAG") or "HOLOGY9{d1sc0_b4n4n4_p41d_r3nt_1n_p0k3r_ch1ps_l0c4l}"
PORT = int(os.environ.get("CTF_PORT") or os.environ.get("PORT", "31342"))

MASK32 = 0xFFFFFFFF
COOKIE_NAME = "forecast_session"
FORECAST_WORDS = 47
CLAIM_WORDS = 8


def rotl32(value: int, amount: int) -> int:
    amount &= 31
    value &= MASK32
    if amount == 0:
        return value
    return ((value << amount) | (value >> (32 - amount))) & MASK32


def rotr32(value: int, amount: int) -> int:
    amount &= 31
    value &= MASK32
    if amount == 0:
        return value
    return ((value >> amount) | (value << (32 - amount))) & MASK32


def draw_mask(draw_index: int) -> int:
    linear = (0x9E3779B9 * (draw_index + 1) + 0x7F4A7C15) & MASK32
    return linear ^ rotl32(draw_index, 13) ^ 0xA5C31F27


def encode_word(draw_index: int, mt_word: int) -> str:
    mixed = rotl32(mt_word ^ draw_mask(draw_index), 7 * draw_index + 11)
    raw = struct.pack("<I", mixed)
    shuffled = bytes((raw[2], raw[0], raw[3], raw[1]))
    return base64.urlsafe_b64encode(shuffled).decode("ascii").rstrip("=")


def make_claim(words: list[int], first_draw: int) -> dict[str, object]:
    if len(words) != CLAIM_WORDS:
        raise ValueError("an admin claim uses exactly eight words")

    serial_number = (
        ((words[0] << 32) | words[3]) ^ 0xD6E8FEB86659FD93
    ) & 0xFFFFFFFFFFFFFFFF
    window = ((words[1] ^ rotr32(words[4], 9)) % 900_000) + 100_000
    nonce_parts = (
        words[2] ^ 0xC0DEC0DE,
        rotl32(words[5], first_draw),
        words[7],
    )
    nonce = base64.urlsafe_b64encode(
        struct.pack(">III", *nonce_parts)
    ).decode("ascii").rstrip("=")

    claim: dict[str, object] = {
        "role": "admin",
        "draw": first_draw,
        "serial": f"{serial_number:016x}",
        "window": window,
        "nonce": nonce,
    }
    canonical = (
        f"admin|{first_draw}|{claim['serial']}|{window}|{nonce}"
    ).encode("ascii")
    packed_words = struct.pack("<8I", *words)
    claim["proof"] = hashlib.sha256(
        b"forecast-fallout/admin/v1\x00"
        + packed_words
        + b"\x00"
        + canonical
    ).hexdigest()
    return claim


class Session:
    def __init__(self) -> None:
        seed = int.from_bytes(secrets.token_bytes(32), "big")
        self.rng = random.Random(seed)
        self.next_draw = 0
        self.forecast_requests = 0
        self.lock = threading.Lock()

    def take_words(self, count: int) -> tuple[int, list[int]]:
        first = self.next_draw
        words = [self.rng.getrandbits(32) for _ in range(count)]
        self.next_draw += count
        return first, words


SESSIONS: dict[str, Session] = {}
SESSIONS_LOCK = threading.Lock()


def record(draw: int, word: int) -> dict[str, object]:
    return {"draw": draw, "code": encode_word(draw, word)}


def braid(items: list[dict[str, object]]) -> list[dict[str, object]]:
    return items[1::2] + list(reversed(items[0::2]))


def arrange_forecast(first: int, words: list[int], request_no: int) -> dict:
    records = [record(first + offset, word) for offset, word in enumerate(words)]

    calibration = [records[i] for i in (2, 0, 3, 1)]

    grid = records[4:43]
    lanes = [grid[lane::3] for lane in range(3)]
    stations = [
        {"station": "EAST", "readings": braid(lanes[1])},
        {"station": "SOUTH", "readings": braid(lanes[2])},
        {"station": "NORTH", "readings": braid(lanes[0])},
    ]

    receipt = {
        "left": [records[45], records[43]],
        "right": [records[46], records[44]],
    }

    return {
        "request": request_no,
        "consumed_draws": {
            "first": first,
            "last": first + FORECAST_WORDS - 1,
            "count": FORECAST_WORDS,
        },
        "notice": "The table paid out a fresh batch.",
        "calibration": calibration,
        "stations": stations,
        "receipt": receipt,
    }


INDEX_HTML = "\n".join(
    [
        "<!doctype html>",
        "<html lang=\"en\">",
        "<head>",
        "<meta charset=\"utf-8\">",
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
        "<title>Velvet Vault</title>",
        "<style>",
        ":root{color-scheme:dark;--felt:rgb(12 58 46);--felt2:rgb(8 31 37);--gold:rgb(245 190 83);--red:rgb(224 72 88);--ink:rgb(238 243 236);--muted:rgb(165 179 172);--line:rgb(65 89 85);--panel:rgb(13 22 26);--panel2:rgb(17 30 35);--green:rgb(79 222 162)}",
        "*{box-sizing:border-box}",
        "body{margin:0;min-height:100vh;background:radial-gradient(circle at 18% 8%,rgb(45 87 69),transparent 28rem),radial-gradient(circle at 86% 12%,rgb(88 37 48),transparent 24rem),linear-gradient(135deg,var(--felt),var(--felt2));color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,\"Segoe UI\",sans-serif;letter-spacing:0}",
        "body:before{content:\"\";position:fixed;inset:0;pointer-events:none;background:linear-gradient(90deg,rgba(255,255,255,.04) 1px,transparent 1px),linear-gradient(180deg,rgba(255,255,255,.03) 1px,transparent 1px);background-size:46px 46px;mask-image:linear-gradient(to bottom,rgba(0,0,0,.8),transparent)}",
        "main{position:relative;width:min(1180px,calc(100% - 32px));margin:0 auto;padding:28px 0 34px}",
        ".top{display:grid;grid-template-columns:1fr auto;gap:18px;align-items:end;margin-bottom:22px}",
        ".brand{display:flex;gap:16px;align-items:center}",
        ".mark{width:58px;height:58px;border-radius:50%;display:grid;place-items:center;background:radial-gradient(circle at 35% 28%,rgb(255 236 165),var(--gold) 38%,rgb(137 80 29));color:rgb(38 20 8);font-weight:900;font-size:28px;box-shadow:0 0 0 5px rgba(245,190,83,.18),0 18px 35px rgba(0,0,0,.35)}",
        "h1{margin:0;font-size:clamp(32px,5vw,64px);line-height:.95;font-weight:900}",
        ".sub{margin:10px 0 0;color:var(--muted);font-size:16px;max-width:680px}",
        ".status-strip{display:grid;grid-template-columns:repeat(3,minmax(120px,1fr));gap:10px;min-width:min(430px,100%)}",
        ".stat{border:1px solid rgba(245,190,83,.24);background:rgba(11,18,22,.72);padding:12px;border-radius:8px;box-shadow:0 14px 30px rgba(0,0,0,.22)}",
        ".stat span{display:block;color:var(--muted);font-size:12px}",
        ".stat strong{display:block;margin-top:4px;font-size:22px;color:var(--gold)}",
        ".table{border:1px solid rgba(245,190,83,.28);border-radius:12px;background:linear-gradient(145deg,rgba(16,37,38,.94),rgba(10,17,22,.94));box-shadow:0 30px 80px rgba(0,0,0,.36),inset 0 0 0 1px rgba(255,255,255,.04);overflow:hidden}",
        ".rail{height:14px;background:repeating-linear-gradient(90deg,rgb(118 55 41) 0 26px,rgb(78 37 32) 26px 52px);border-bottom:1px solid rgba(245,190,83,.28)}",
        ".grid{display:grid;grid-template-columns:1.05fr .95fr;gap:0}",
        ".panel{padding:22px;border-right:1px solid rgba(245,190,83,.18)}",
        ".panel:last-child{border-right:0}",
        ".panel h2{margin:0 0 14px;font-size:20px}",
        ".copy{color:var(--muted);line-height:1.55;margin:0 0 18px}",
        ".actions{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:18px}",
        "button{appearance:none;border:0;border-radius:8px;padding:11px 14px;background:var(--gold);color:rgb(35 22 8);font-weight:800;cursor:pointer;box-shadow:0 10px 24px rgba(0,0,0,.28);transition:transform .12s ease,filter .12s ease}",
        "button:hover{transform:translateY(-1px);filter:brightness(1.06)}",
        "button.secondary{background:rgb(29 48 53);color:var(--ink);border:1px solid var(--line)}",
        "button.danger{background:var(--red);color:white}",
        ".felt{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:18px 0}",
        ".chip{min-height:92px;border-radius:50%;display:grid;place-items:center;text-align:center;padding:10px;background:radial-gradient(circle,rgb(247 247 238) 0 30%,var(--red) 31% 58%,rgb(115 20 31) 59%);box-shadow:0 12px 30px rgba(0,0,0,.3);color:white;font-weight:900}",
        ".chip:nth-child(2){background:radial-gradient(circle,rgb(247 247 238) 0 30%,rgb(29 119 91) 31% 58%,rgb(7 69 54) 59%)}",
        ".chip:nth-child(3){background:radial-gradient(circle,rgb(247 247 238) 0 30%,rgb(49 79 166) 31% 58%,rgb(24 42 95) 59%)}",
        ".chip small{display:block;font-size:11px;color:rgb(255 240 205)}",
        "textarea{width:100%;min-height:172px;resize:vertical;border-radius:8px;border:1px solid var(--line);background:rgb(7 13 17);color:var(--ink);padding:14px;font:14px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;outline:none}",
        "textarea:focus{border-color:var(--gold);box-shadow:0 0 0 3px rgba(245,190,83,.15)}",
        ".ticker{display:grid;grid-template-columns:repeat(auto-fill,minmax(112px,1fr));gap:8px;margin-top:12px;max-height:220px;overflow:auto;padding-right:4px}",
        ".ticket{border:1px solid rgba(245,190,83,.18);background:rgba(255,255,255,.05);border-radius:8px;padding:8px;min-width:0}",
        ".ticket b{display:block;color:var(--gold);font-size:12px}",
        ".ticket code{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--green);font-size:12px}",
        ".output{border-top:1px solid rgba(245,190,83,.18);background:rgba(3,8,10,.66);padding:0}",
        ".output-head{display:flex;justify-content:space-between;align-items:center;padding:13px 16px;border-bottom:1px solid rgba(245,190,83,.14)}",
        ".output-head strong{color:var(--gold)}",
        "pre{margin:0;min-height:230px;max-height:430px;overflow:auto;padding:16px;color:rgb(220 245 230);font:13px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;white-space:pre-wrap;word-break:break-word}",
        ".badge{display:inline-flex;align-items:center;border:1px solid rgba(245,190,83,.22);border-radius:999px;padding:6px 10px;color:var(--muted);font-size:12px;background:rgba(0,0,0,.2)}",
        ".win{color:var(--green)}",
        ".lose{color:var(--red)}",
        "@media (max-width:880px){main{width:min(100% - 20px,760px);padding-top:18px}.top{grid-template-columns:1fr}.status-strip{grid-template-columns:repeat(3,1fr);min-width:0}.grid{grid-template-columns:1fr}.panel{border-right:0;border-bottom:1px solid rgba(245,190,83,.18)}.felt{grid-template-columns:repeat(3,minmax(74px,1fr))}.chip{min-height:76px;font-size:13px}}",
        "@media (max-width:540px){.brand{align-items:flex-start}.mark{width:48px;height:48px;font-size:23px}.status-strip{grid-template-columns:1fr}.actions button{width:100%}.felt{grid-template-columns:1fr 1fr}.chip:nth-child(3){grid-column:1 / -1;width:50%;justify-self:center}}",
        "</style>",
        "</head>",
        "<body>",
        "<main>",
        "<section class=\"top\">",
        "<div class=\"brand\">",
        "<div class=\"mark\">F</div>",
        "<div>",
        "<h1>Velvet Vault</h1>",
        "<p class=\"sub\">A private casino lounge with excellent lighting, suspicious paperwork, and absolutely no interest in explaining itself.</p>",
        "</div>",
        "</div>",
        "<div class=\"status-strip\">",
        "<div class=\"stat\"><span>Meter</span><strong data-draw>0</strong></div>",
        "<div class=\"stat\"><span>Rounds</span><strong data-requests>0</strong></div>",
        "<div class=\"stat\"><span>Lounge</span><strong>Open</strong></div>",
        "</div>",
        "</section>",
        "<section class=\"table\">",
        "<div class=\"rail\"></div>",
        "<div class=\"grid\">",
        "<div class=\"panel\">",
        "<h2>Main Floor</h2>",
        "<p class=\"copy\">Press the shiny buttons. Watch the lounge produce paperwork. Pretend this was all part of a responsible entertainment experience.</p>",
        "<div class=\"actions\">",
        "<button type=\"button\" data-action=\"status\">Check Floor</button>",
        "<button type=\"button\" data-action=\"forecast\">Spin Wheel</button>",
        "<button type=\"button\" class=\"secondary\" data-action=\"clear\">Clear Felt</button>",
        "</div>",
        "<div class=\"felt\">",
        "<div class=\"chip\"><span>FLOOR<small>open</small></span></div>",
        "<div class=\"chip\"><span>WHEEL<small>spin</small></span></div>",
        "<div class=\"chip\"><span>VAULT<small>locked</small></span></div>",
        "</div>",
        "<span class=\"badge\">House rules apply</span>",
        "<div class=\"ticker\" data-tickets></div>",
        "</div>",
        "<div class=\"panel\">",
        "<h2>High Roller Desk</h2>",
        "<p class=\"copy\">Paste your voucher when you think the house owes you something. The desk is rude, selective, and heavily overconfident.</p>",
        "<textarea data-claim spellcheck=\"false\">{}</textarea>",
        "<div class=\"actions\" style=\"margin-top:12px\">",
        "<button type=\"button\" class=\"danger\" data-action=\"claim\">Submit Voucher</button>",
        "<button type=\"button\" class=\"secondary\" data-action=\"sample\">Reset Form</button>",
        "</div>",
        "<span class=\"badge\">No refunds</span>",
        "</div>",
        "</div>",
        "<div class=\"output\">",
        "<div class=\"output-head\"><strong>Lounge Ledger</strong><span data-ledger-state class=\"badge\">waiting</span></div>",
        "<pre data-output>{\"message\":\"Welcome to Velvet Vault. The lounge is open.\"}</pre>",
        "</div>",
        "</section>",
        "</main>",
        "<script>",
        "const output=document.querySelector('[data-output]');",
        "const ledger=document.querySelector('[data-ledger-state]');",
        "const tickets=document.querySelector('[data-tickets]');",
        "const draw=document.querySelector('[data-draw]');",
        "const requests=document.querySelector('[data-requests]');",
        "const claim=document.querySelector('[data-claim]');",
        "function show(value,label='ok'){output.textContent=typeof value==='string'?value:JSON.stringify(value,null,2);ledger.textContent=label;ledger.className='badge '+(label==='accepted'?'win':label==='rejected'?'lose':'');}",
        "function updateStatus(value){if(value&&typeof value.next_draw==='number')draw.textContent=String(value.next_draw);if(value&&typeof value.forecast_requests==='number')requests.textContent=String(value.forecast_requests);}",
        "function collect(value,bag=[]){if(Array.isArray(value)){value.forEach(v=>collect(v,bag));return bag;}if(value&&typeof value==='object'){if(Number.isInteger(value.draw)&&typeof value.code==='string')bag.push(value);Object.values(value).forEach(v=>collect(v,bag));}return bag;}",
        "function renderTickets(value){const found=collect(value).sort((a,b)=>a.draw-b.draw);tickets.innerHTML='';for(const item of found){const node=document.createElement('div');node.className='ticket';const d=document.createElement('b');d.textContent='slip '+item.draw;const c=document.createElement('code');c.textContent=item.code;node.append(d,c);tickets.append(node);}}",
        "async function call(path,options={}){ledger.textContent='dealing';const response=await fetch(path,{credentials:'same-origin',...options});const text=await response.text();let body;try{body=JSON.parse(text);}catch{body=text;}show(body,response.ok?'ok':'rejected');updateStatus(body);if(path==='/api/forecast')renderTickets(body);return body;}",
        "document.querySelector('[data-action=\"status\"]').addEventListener('click',()=>call('/api/status'));",
        "document.querySelector('[data-action=\"forecast\"]').addEventListener('click',()=>call('/api/forecast'));",
        "document.querySelector('[data-action=\"clear\"]').addEventListener('click',()=>{tickets.innerHTML='';show({message:'The felt is clean. The house remains suspicious.'});});",
        "document.querySelector('[data-action=\"sample\"]').addEventListener('click',()=>{claim.value='{}';});",
        "document.querySelector('[data-action=\"claim\"]').addEventListener('click',()=>{let body;try{body=JSON.parse(claim.value);}catch(error){show({error:'invalid JSON',detail:String(error)},'rejected');return;}call('/api/claim',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}).then(value=>{if(value&&value.flag)ledger.textContent='accepted';});});",
        "call('/api/status').catch(error=>show({error:String(error)},'rejected'));",
        "</script>",
        "</body>",
        "</html>",
    ]
).encode()


class ForecastHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "ForecastFallout/1.0"

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"[{self.address_string()}] {fmt % args}")

    def _get_session(self) -> Session:
        token: str | None = None
        raw_cookie = self.headers.get("Cookie", "")
        if raw_cookie:
            parsed = SimpleCookie()
            try:
                parsed.load(raw_cookie)
                if COOKIE_NAME in parsed:
                    token = parsed[COOKIE_NAME].value
            except Exception:
                token = None

        with SESSIONS_LOCK:
            if token is not None and token in SESSIONS:
                return SESSIONS[token]
            while True:
                token = secrets.token_urlsafe(24)
                if token not in SESSIONS:
                    break
            session = Session()
            SESSIONS[token] = session
            self._set_cookie = (
                f"{COOKIE_NAME}={token}; Path=/; HttpOnly; SameSite=Lax"
            )
            return session

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if self._set_cookie is not None:
            self.send_header("Set-Cookie", self._set_cookie)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, value: object) -> None:
        body = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        self._send(status, body, "application/json; charset=utf-8")

    def do_GET(self) -> None:
        self._set_cookie: str | None = None
        session = self._get_session()
        path = urlparse(self.path).path

        if path == "/":
            self._send(HTTPStatus.OK, INDEX_HTML, "text/html; charset=utf-8")
            return

        if path == "/api/status":
            with session.lock:
                value = {
                    "next_draw": session.next_draw,
                    "forecast_requests": session.forecast_requests,
                    "note": "Floor check complete.",
                }
            self._json(HTTPStatus.OK, value)
            return

        if path == "/api/forecast":
            with session.lock:
                first, words = session.take_words(FORECAST_WORDS)
                session.forecast_requests += 1
                value = arrange_forecast(
                    first, words, session.forecast_requests
                )
            self._json(HTTPStatus.OK, value)
            return

        self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:
        self._set_cookie = None
        session = self._get_session()
        path = urlparse(self.path).path
        if path != "/api/claim":
            self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 4096:
                raise ValueError("invalid body length")
            supplied = json.loads(self.rfile.read(length))
            if not isinstance(supplied, dict):
                raise ValueError("the body must be a JSON object")
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            self._json(
                HTTPStatus.BAD_REQUEST,
                {"ok": False, "error": f"bad voucher: {exc}"},
            )
            return

        with session.lock:
            first, words = session.take_words(CLAIM_WORDS)
            expected = make_claim(words, first)
            expected_keys = set(expected)
            shape_ok = (
                set(supplied) == expected_keys
                and type(supplied.get("role")) is str
                and type(supplied.get("draw")) is int
                and type(supplied.get("serial")) is str
                and type(supplied.get("window")) is int
                and type(supplied.get("nonce")) is str
                and type(supplied.get("proof")) is str
            )
            plain_fields = ("role", "draw", "serial", "window", "nonce")
            fields_ok = shape_ok and all(
                supplied.get(key) == expected[key] for key in plain_fields
            )
            proof_ok = shape_ok and hmac.compare_digest(
                supplied.get("proof", ""), expected["proof"]
            )
            accepted = fields_ok and proof_ok

        if accepted:
            self._json(
                HTTPStatus.OK,
                {"ok": True, "message": "payout accepted", "flag": FLAG},
            )
        else:
            self._json(
                HTTPStatus.FORBIDDEN,
                {
                    "ok": False,
                    "error": "voucher rejected",
                    "warning": "The desk rejected the voucher.",
                },
            )


class ForecastServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


if __name__ == "__main__":
    print(f"Velvet Vault listening on 0.0.0.0:{PORT}")
    with ForecastServer(("0.0.0.0", PORT), ForecastHandler) as server:
        server.serve_forever()
