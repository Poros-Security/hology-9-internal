from collections import deque
from http.cookiejar import CookieJar
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener
import json
import sys
import time


FILES = "abcdefgh"
RANKS = "12345678"
LIMIT = 5
QUEEN = [
    (1, 0), (-1, 0), (0, 1), (0, -1),
    (1, 1), (1, -1), (-1, 1), (-1, -1),
]
KNIGHT = [
    (1, 2), (2, 1), (-1, 2), (-2, 1),
    (1, -2), (2, -1), (-1, -2), (-2, -1),
]
VALUE = {
    "Q": 9, "R": 5, "B": 3, "N": 3, "P": 1,
    "q": 9, "r": 5, "b": 3, "n": 3, "p": 1,
}


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


def search(code, limit):
    start = load(code)
    queue = deque([(start, [])])
    seen = {(dump(start), 0)}

    while queue:
        board, route = queue.popleft()
        if len(route) >= limit:
            continue
        for play in legal(board, "w"):
            after = apply(board, play)
            if trapped(after):
                return route + [play]
            after, reply = bot(after)
            key = (dump(after), len(route) + 1)
            if key not in seen:
                seen.add(key)
                queue.append((after, route + [play]))
    raise RuntimeError("no route found")


def fetch(opener, base, path, body=None):
    payload = None
    headers = {}
    if body is not None:
        payload = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    request = Request(base.rstrip("/") + path, payload, headers)
    try:
        with opener.open(request, timeout=10) as response:
            return json.loads(response.read().decode())
    except HTTPError as error:
        return json.loads(error.read().decode())


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8085"
    opener = build_opener(HTTPCookieProcessor(CookieJar()))
    state = fetch(opener, base, "/api/new")
    while not state["won"]:
        if state["over"]:
            raise SystemExit(f"run lost on round {state['round']}: {state['lost']}")
        if state["cleared"]:
            state = fetch(opener, base, "/api/next", {})
            continue
        began = time.time()
        route = search(state["board"], state["limit"] - state["turn"])
        print(f"round {state['round']}/{state['rounds']}: {' '.join(route)} "
              f"({time.time() - began:.1f}s, {state['remaining']}s on clock)")
        for play in route:
            state = fetch(opener, base, "/api/move", {"move": play})
        print("  magnus:", state["note"])
    print("flag =", state["flag"])


if __name__ == "__main__":
    main()
