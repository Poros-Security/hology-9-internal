from http.cookies import SimpleCookie
from pathlib import Path
from socketserver import ThreadingMixIn
from urllib.parse import parse_qs
from wsgiref.simple_server import WSGIServer, make_server
import json
import os
import secrets
import threading
import time


FLAG = os.environ.get("GZCTF_FLAG") or os.environ.get("FLAG") or "HOLOGY9{redacted}"
PORT = int(os.environ.get("PORT", "8085"))
ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
FILES = "abcdefgh"
RANKS = "12345678"
LIMIT = 5
TIERS = [3] * 4 + [4] * 3
ROUNDS = len(TIERS)
ROUND_SECONDS = int(os.environ.get("ROUND_SECONDS", "120"))
NEW_DELAY = 3
QUEEN = [
    (1, 0), (-1, 0), (0, 1), (0, -1),
    (1, 1), (1, -1), (-1, 1), (-1, -1),
]
KNIGHT = [
    (1, 2), (2, 1), (-1, 2), (-2, 1),
    (1, -2), (2, -1), (-1, -2), (-2, -1),
]
GLYPH = {
    "K": "♔", "Q": "♕", "R": "♖", "B": "♗", "N": "♘", "P": "♙",
    "k": "♚", "q": "♛", "r": "♜", "b": "♝", "n": "♞", "p": "♟",
}
VALUE = {
    "Q": 9, "R": 5, "B": 3, "N": 3, "P": 1,
    "q": 9, "r": 5, "b": 3, "n": 3, "p": 1,
}
PUZZLES = json.loads((ROOT / "puzzles.json").read_text())
BANK = {depth: [item for item in PUZZLES if item["depth"] == depth] for depth in set(TIERS)}
if not all(BANK.values()):
    raise SystemExit(f"puzzles.json needs boards for every tier in {sorted(set(TIERS))}")
TALK = {
    "start": [
        "Seven games. I've played more before breakfast.",
        "Fine. Let's make this quick.",
        "Another challenger. Sure, I have time.",
        "I'll go easy on you. I won't, but I'll say it.",
    ],
    "reply": [
        "Seen it.",
        "Book.",
        "That's theory, by the way.",
        "Interesting. Wrong, but interesting.",
        "I calculated that before you sat down.",
        "Did your cat play that one?",
        "Bold.",
        "My king is fine. Thanks for asking.",
        "I'd resign here. If I were you.",
        "Hm.",
        "Cute.",
        "I've had harder games in a bullet queue at 3am.",
        "You're playing the board. I'm playing you.",
        "Every piece you own is a queen and you still can't find it.",
        "Take your time. Actually, don't.",
        "Nice try. No, really.",
        "I'm not worried. This is my worried face though.",
        "Is this an opening or a cry for help?",
    ],
    "check": [
        "A check. Very brave.",
        "Checks are free. Mate costs extra.",
        "Tickles.",
        "That's it? That's the attack?",
    ],
    "round": {
        2: "Okay, that one was a warm-up. For me.",
        3: "Still here? Bold.",
        4: "I'm just letting you build confidence.",
        5: "Fine. Gloves off. No more easy ones.",
        6: "You're not supposed to be here.",
        7: "Last board. Nobody gets this far. Nobody.",
    },
    "cleared": {
        1: "Lucky. The board was rigged.",
        2: "I wasn't even looking.",
        3: "Okay, that was decent. Don't tell anyone I said that.",
        4: "Four. Cute. Now the real ones.",
        5: "Okay. Now I'm taking this seriously.",
        6: "Who taught you this? Tell them to stop.",
    },
    "won": "That's it. I'm not playing this variant anymore.",
    "moves": [
        "Out of moves. Shame.",
        "All those moves and nothing. I've seen pigeons do better.",
        "That's what happens when you play on vibes.",
    ],
    "time": [
        "Clock's a piece too.",
        "Flag fell. Very sad.",
        "You were thinking? I couldn't tell.",
    ],
}
SESSIONS = {}
NEW_TIMES = {}
DECKS = {}
LOCK = threading.Lock()
MIMES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
}


class ThreadedServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True
    allow_reuse_address = True


def inside(x, y):
    return 0 <= x < 8 and 0 <= y < 8


def square(x, y):
    return FILES[x] + RANKS[y]


def coord(item):
    return FILES.index(item[0]), RANKS.index(item[1])


def color(piece):
    return "w" if piece.isupper() else "b"


def enemy(first, second):
    return color(first) != color(second)


def load(code):
    board = {}
    for index, piece in enumerate(code):
        if piece != ".":
            board[square(index % 8, index // 8)] = piece
    return board


def dump(board):
    return "".join(board.get(square(x, y), ".") for y in range(8) for x in range(8))


def find(board, piece):
    for spot, found in board.items():
        if found == piece:
            return spot
    return None


def apply(board, play):
    nextboard = dict(board)
    piece = nextboard.pop(play[:2])
    nextboard[play[2:]] = piece
    return nextboard


def attack(board, origin, target):
    piece = board.get(origin)
    if not piece:
        return False

    x, y = coord(origin)
    tx, ty = coord(target)
    dx = tx - x
    dy = ty - y

    if piece.upper() == "N":
        return (abs(dx), abs(dy)) in ((1, 2), (2, 1))
    if piece.upper() == "K":
        return max(abs(dx), abs(dy)) == 1 and (dx != 0 or dy != 0)
    if dx == 0 and dy == 0:
        return False
    if dx != 0 and dy != 0 and abs(dx) != abs(dy):
        return False

    stepx = 0 if dx == 0 else (1 if dx > 0 else -1)
    stepy = 0 if dy == 0 else (1 if dy > 0 else -1)
    x += stepx
    y += stepy
    while (x, y) != (tx, ty):
        if board.get(square(x, y)):
            return False
        x += stepx
        y += stepy
    return True


def check(board, team):
    king = find(board, "k" if team == "b" else "K")
    if not king:
        return False
    for spot, piece in board.items():
        if color(piece) != team and attack(board, spot, king):
            return True
    return False


def pseudo(board, origin, piece):
    moves = []
    x, y = coord(origin)
    steps = KNIGHT if piece.upper() == "N" else QUEEN
    single = piece.upper() in "NK"

    for dx, dy in steps:
        nx = x + dx
        ny = y + dy
        while inside(nx, ny):
            target = square(nx, ny)
            found = board.get(target)
            if found:
                if enemy(piece, found) and found.upper() != "K":
                    moves.append(origin + target)
                break
            moves.append(origin + target)
            if single:
                break
            nx += dx
            ny += dy
    return moves


def legal(board, team):
    moves = []
    for origin, piece in sorted(board.items()):
        if color(piece) != team:
            continue
        for play in pseudo(board, origin, piece):
            nextboard = apply(board, play)
            if not check(nextboard, team):
                moves.append(play)
    return sorted(set(moves))


def trapped(board):
    if not check(board, "b"):
        return False
    king = find(board, "k")
    if not king:
        return False
    for play in legal(board, "b"):
        if play[:2] == king:
            return False
    return True


def bot(board):
    if trapped(board):
        return board, "resigns"

    moves = legal(board, "b")
    if not moves:
        return board, "blinks"

    if check(board, "b"):
        king = find(board, "k")
        escapes = [play for play in moves if play[:2] == king]
        if escapes:
            play = sorted(escapes, key=lambda item: (item[2:], item[:2]))[0]
            return apply(board, play), play

    captures = []
    for play in moves:
        target = board.get(play[2:])
        if target and target.isupper():
            captures.append((-VALUE.get(target, 0), play))
    if captures:
        play = sorted(captures)[0][1]
        return apply(board, play), play

    play = moves[0]
    return apply(board, play), play


def pieces(board):
    items = []
    for spot, piece in sorted(board.items()):
        items.append({
            "square": spot,
            "piece": piece,
            "glyph": GLYPH[piece],
            "side": "white" if piece.isupper() else "black",
        })
    return items


def remaining(game):
    if game["over"] or game["cleared"]:
        return None
    return max(0.0, round(game["deadline"] - time.monotonic(), 1))


def view(game):
    board = load(game["board"])
    return {
        "board": game["board"],
        "pieces": pieces(board),
        "turn": game["turn"],
        "limit": game["limit"],
        "round": game["round"],
        "rounds": ROUNDS,
        "streak": game["streak"],
        "cleared": game["cleared"],
        "remaining": remaining(game),
        "seconds": ROUND_SECONDS,
        "won": game["won"],
        "over": game["over"],
        "lost": game["lost"],
        "flag": FLAG if game["won"] else None,
        "puzzle": game["puzzle"],
        "note": game["note"],
        "log": game["log"][-40:],
        "run": game["run"],
        "check": check(board, "b"),
    }


def shuffle(sid, tier):
    deck = list(range(len(BANK[tier])))
    secrets.SystemRandom().shuffle(deck)
    DECKS[(sid, tier)] = deck


def choose(sid, tier, previous=None):
    pool = BANK[tier]
    if not DECKS.get((sid, tier)):
        shuffle(sid, tier)
    deck = DECKS[(sid, tier)]
    if previous is not None and len(deck) > 1 and pool[deck[0]]["board"] == previous:
        deck.append(deck.pop(0))
    return pool[deck.pop(0)]


def token(environ):
    raw = environ.get("HTTP_COOKIE", "")
    jar = SimpleCookie()
    if raw:
        jar.load(raw)
    if "sid" in jar:
        return jar["sid"].value
    return secrets.token_hex(16)


def post(game, who, text=None, move=None, tone=None):
    game["seq"] += 1
    game["log"].append({"n": game["seq"], "who": who, "move": move, "text": text, "tone": tone})


def say(game, line, move=None):
    game["note"] = line
    post(game, "magnus", line, move)


def deal(sid, game):
    puzzle = choose(sid, TIERS[game["round"] - 1], game.get("board"))
    game["board"] = puzzle["board"]
    game["puzzle"] = puzzle["name"]
    game["limit"] = puzzle.get("limit", LIMIT)
    game["turn"] = 0
    game["cleared"] = False
    game["deadline"] = time.monotonic() + ROUND_SECONDS


def announce(game):
    post(game, "system", f"Round {game['round']} of {ROUNDS}")


def begin(sid):
    game = {
        "board": SESSIONS.get(sid, {}).get("board"),
        "run": secrets.token_hex(4),
        "seq": 0,
        "round": 1,
        "streak": 0,
        "won": False,
        "over": False,
        "lost": None,
        "log": [],
    }
    deal(sid, game)
    post(game, "system", "Magnus Carlsen joined the board.")
    announce(game)
    say(game, secrets.choice(TALK["start"]))
    SESSIONS[sid] = game
    return game


def lose(game, reason):
    game["over"] = True
    game["lost"] = reason
    post(game, "system", f"Run over at round {game['round']}.", tone="bad")
    say(game, secrets.choice(TALK[reason]))


def expire(game):
    if not game["over"] and not game["cleared"] and time.monotonic() > game["deadline"]:
        lose(game, "time")


def session(environ, sid=None):
    if sid is None:
        sid = token(environ)
    if sid not in SESSIONS:
        begin(sid)
    current = SESSIONS[sid]
    expire(current)
    return sid, current


def data(environ):
    size = min(int(environ.get("CONTENT_LENGTH") or "0"), 4096)
    raw = environ["wsgi.input"].read(size) if size else b"{}"
    try:
        return json.loads(raw.decode())
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def send(start, status, body, mime="application/json; charset=utf-8", sid=None):
    headers = [
        ("Content-Type", mime),
        ("Cache-Control", "no-store"),
    ]
    if sid:
        headers.append(("Set-Cookie", f"sid={sid}; Path=/; SameSite=Lax"))
    start(status, headers)
    if isinstance(body, (dict, list)):
        payload = json.dumps(body).encode()
    elif isinstance(body, str):
        payload = body.encode()
    else:
        payload = body
    return [payload]


def asset(start, path):
    if path == "/":
        target = STATIC / "index.html"
    else:
        target = (STATIC / path.lstrip("/")).resolve()
        if STATIC.resolve() not in target.parents:
            return send(start, "403 Forbidden", "no", "text/plain; charset=utf-8")
    if not target.exists() or not target.is_file():
        return send(start, "404 Not Found", "missing", "text/plain; charset=utf-8")
    return send(start, "200 OK", target.read_bytes(), MIMES.get(target.suffix, "application/octet-stream"))


def api(environ, start, body):
    path = environ.get("PATH_INFO", "")
    query = parse_qs(environ.get("QUERY_STRING", ""))

    if path == "/api/new":
        sid = token(environ)
        now = time.monotonic()
        if sid in SESSIONS and now < NEW_TIMES.get(sid, 0):
            sid, current = session(environ, sid)
            current["note"] = "Wait 3 seconds before starting a new game."
            post(current, "system", current["note"], tone="bad")
            return send(start, "429 Too Many Requests", view(current), sid=sid)
        NEW_TIMES[sid] = now + NEW_DELAY
        current = begin(sid)
        return send(start, "200 OK", view(current), sid=sid)

    if path == "/api/state":
        sid, current = session(environ)
        if "fresh" in query and current["over"] and not current["won"]:
            current = begin(sid)
        return send(start, "200 OK", view(current), sid=sid)

    if environ.get("REQUEST_METHOD") != "POST" or path not in ("/api/move", "/api/next"):
        return send(start, "404 Not Found", {"error": "missing"})

    sid, current = session(environ)

    if path == "/api/next":
        if current["over"] or not current["cleared"]:
            return send(start, "409 Conflict", view(current), sid=sid)
        current["round"] += 1
        deal(sid, current)
        announce(current)
        say(current, TALK["round"][current["round"]])
        return send(start, "200 OK", view(current), sid=sid)

    if current["over"] or current["cleared"]:
        return send(start, "409 Conflict", view(current), sid=sid)

    play = str(body.get("move", "")).strip().lower()
    board = load(current["board"])
    if len(play) != 4 or play[:2] not in board or play not in legal(board, "w"):
        current["note"] = "Invalid move."
        post(current, "system", f"Invalid move: {play or '?'}", tone="bad")
        return send(start, "400 Bad Request", view(current), sid=sid)

    board = apply(board, play)
    current["turn"] += 1
    current["board"] = dump(board)
    post(current, "you", move=play)

    if trapped(board):
        current["streak"] += 1
        post(current, "system", f"Round {current['round']} cleared.", tone="good")
        if current["streak"] >= ROUNDS:
            current["won"] = True
            current["over"] = True
            say(current, TALK["won"])
            post(current, "system", "Magnus Carlsen left the game.", tone="good")
        else:
            current["cleared"] = True
            say(current, TALK["cleared"][current["streak"]])
        return send(start, "200 OK", view(current), sid=sid)

    if current["turn"] >= current["limit"]:
        lose(current, "moves")
        return send(start, "200 OK", view(current), sid=sid)

    pressed = check(board, "b")
    board, reply = bot(board)
    line = secrets.choice(TALK["check" if pressed else "reply"])
    current["board"] = dump(board)
    say(current, line, reply if len(reply) == 4 else None)
    return send(start, "200 OK", view(current), sid=sid)


def app(environ, start):
    path = environ.get("PATH_INFO", "/")
    if not path.startswith("/api/"):
        return asset(start, path)
    body = data(environ) if environ.get("REQUEST_METHOD") == "POST" else {}
    with LOCK:
        return api(environ, start, body)


def main():
    with make_server("0.0.0.0", PORT, app, server_class=ThreadedServer) as server:
        print(f"serving http://127.0.0.1:{PORT}", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
