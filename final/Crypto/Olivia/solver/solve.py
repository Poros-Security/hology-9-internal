from pathlib import Path
from itertools import combinations, product
import ast

from Crypto.Cipher import AES
from Crypto.Hash import SHA256


DOMAIN = b"committee-polynomial-v1"


def parse():
    path = Path(__file__).resolve().parents[1] / "dist" / "output.txt"
    data = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        label, item = line.split("=", 1)
        data[label.strip()] = ast.literal_eval(item.strip())
    return data


def pairs(total):
    return [(left, right) for left in range(total) for right in range(left, total)]


def split(data):
    total = data["variables"]
    quiet = data["quiet"]
    edges = set()
    order = pairs(total)

    for poly in data["equations"]:
        for coeff, pair in zip(poly["quad"], order):
            left, right = pair
            if left != right and coeff % data["field"]:
                edges.add(pair)

    for choice in combinations(range(total), quiet):
        trial = set(choice)
        ok = True
        for left, right in combinations(choice, 2):
            if (min(left, right), max(left, right)) in edges:
                ok = False
                break
        if ok:
            return list(choice), [item for item in range(total) if item not in trial]

    raise RuntimeError("could not find the quiet block")


def solve(rows, mod):
    height = len(rows)
    width = len(rows[0]) - 1
    mat = [row[:] for row in rows]
    pivot = [-1] * width
    rank = 0

    for col in range(width):
        found = None
        for row in range(rank, height):
            if mat[row][col] % mod:
                found = row
                break
        if found is None:
            continue

        mat[rank], mat[found] = mat[found], mat[rank]
        inv = pow(mat[rank][col] % mod, -1, mod)
        mat[rank] = [(item * inv) % mod for item in mat[rank]]

        for row in range(height):
            if row == rank:
                continue
            factor = mat[row][col] % mod
            if factor:
                mat[row] = [
                    (current - factor * base) % mod
                    for current, base in zip(mat[row], mat[rank])
                ]

        pivot[col] = rank
        rank += 1

    for row in range(rank, height):
        if all(mat[row][col] % mod == 0 for col in range(width)):
            if mat[row][-1] % mod:
                return None

    if any(item == -1 for item in pivot):
        return None

    result = [0] * width
    for col, row in enumerate(pivot):
        result[col] = mat[row][-1] % mod
    return result


def rows(data, quiet, loud, guess):
    mod = data["field"]
    order = pairs(data["variables"])
    place = {name: index for index, name in enumerate(quiet)}
    fixed = dict(zip(loud, guess))
    rows = []

    for poly, target in zip(data["equations"], data["target"]):
        rhs = (target - poly["bias"]) % mod
        coeffs = [0] * len(quiet)

        for var, coeff in enumerate(poly["linear"]):
            if var in place:
                coeffs[place[var]] = (coeffs[place[var]] + coeff) % mod
            else:
                rhs = (rhs - coeff * fixed[var]) % mod

        for coeff, (left, right) in zip(poly["quad"], order):
            coeff %= mod
            if not coeff:
                continue

            leftfree = left in place
            rightfree = right in place

            if leftfree and rightfree:
                return None
            if leftfree:
                coeffs[place[left]] = (
                    coeffs[place[left]] + coeff * fixed[right]
                ) % mod
            elif rightfree:
                coeffs[place[right]] = (
                    coeffs[place[right]] + coeff * fixed[left]
                ) % mod
            else:
                rhs = (rhs - coeff * fixed[left] * fixed[right]) % mod

        rows.append(coeffs + [rhs])

    return rows


def check(data, point):
    mod = data["field"]
    order = pairs(data["variables"])
    out = []
    for poly in data["equations"]:
        total = poly["bias"]
        for var, coeff in enumerate(poly["linear"]):
            total += coeff * point[var]
        for coeff, (left, right) in zip(poly["quad"], order):
            total += coeff * point[left] * point[right]
        out.append(total % mod)
    return out == data["target"]


def recover(data):
    quiet, loud = split(data)
    mod = data["field"]

    for guess in product(range(mod), repeat=len(loud)):
        system = rows(data, quiet, loud, guess)
        if system is None:
            continue

        free = solve(system, mod)
        if free is None:
            continue

        point = [0] * data["variables"]
        for var, item in zip(loud, guess):
            point[var] = item
        for var, item in zip(quiet, free):
            point[var] = item

        if check(data, point):
            return point

    raise RuntimeError("no signature found")


def unseal(data, point):
    key = SHA256.new(bytes(point) + DOMAIN).digest()
    box = AES.new(key, AES.MODE_GCM, nonce=bytes.fromhex(data["nonce"]))
    return box.decrypt_and_verify(
        bytes.fromhex(data["ciphertext"]),
        bytes.fromhex(data["tag"]),
    )


def main():
    data = parse()
    point = recover(data)
    flag = unseal(data, point)
    print(f"signature = {point}")
    print(f"flag = {flag.decode()}")


if __name__ == "__main__":
    main()
