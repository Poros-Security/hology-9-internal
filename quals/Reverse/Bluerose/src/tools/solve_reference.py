#!/usr/bin/env python3
"""Compact solver for normal and xollvm builds: hashes -> moves -> key -> flag."""

import argparse
import base64
import hashlib
import hmac
from pathlib import Path
import struct

import chess

MASK = (1 << 64) - 1
INITIAL = (0x243F6A8885A308D3, 0x13198A2E03707344,
           0xA4093822299F31D0, 0x082EFA98EC4E6C89)

# Recovered target hashes and encoded black replies. This is not a move list:
# each white move must be found by hashing the legal successor positions.
TARGET_DATA = base64.b85decode("""
Of0viHCh49Xb#E!Y4{R%`n6>(J>8w*mXPz`<194N$*zyT5PR<p$(K3*vMYI!EDf~H!*X^6+R-8kqivxj+|Kz|_Yc_ad8L5HFKQqx
dg*R;3aoL>{|z7%?T}J)hQB!u2AgmOQjqI<_YaS)lrB(WzC~#a%=__pwEGXBT?w9dn%+nriH~>=vcTqjAc^6Qtq*{ho<GIL#!8$B
8Iuf;Ff6o@{|#K!oFNgzp}(;X-WvSW^pemhdJNDqGsuO9t6yOX6->+D{=U?7vkssOig{O)lGy4DB<8NeIt}!s^A5?oFsNPR+t&LG
TwWYn6z>cGbPsZ4w4Y#TdYU2!jKl?dnRZpm`VQFqZV>jCPRQpAnksCS7*T?Su?Q18t;-%Ndj1&=fI;``$L(Zsa|<U3La?JUukk1j
Z<q+!?BioIyABbC4Tr*F>d^TPM^9x`>b<}Q<P20;ZsmQC(PVHA;@W-qv|!;7?+@kC4-wF{AUF35pemW6@&d&)?+u396I6W0x;bkM
pbE_Gsps4c^$L=XJiU51Qb>OdeXKQvK{$h8I1DKS2hj}86X!7wIu^{uh?SI2GYNXGRE`0)+<bTpa1$T!IZ9G3QU=f*6`c?7MXfpx
wMj-FHQipBI0`b!Bk^bR%VXjkjs9vvgpe#6vkqF+f(m5>#a{aijZJzud{rm6iv;rgq&FKJ|NZqJ95EX=0#dthIu1A0j_qdCAGYfb
_II&(l4PvO^a`y>l@TH9Xud5Cy?9*itWENQGY?24@O__Sfa<so+CCA^;0rK|WDQ%%Vv~qtJcBg}@sLq>X-&KN`V1>Zy*h~uN?%zB
i;9G~|1)Sr!~$AA3hCB4P}XY=<m+kxv6lf(vkFOV=F85d?D~5Pfm6B;)N);Wu?}p*`^jwwqV;+V1eG^_ap$I_?G8dCDB23+kTd@a
byvt`#Nu5%dkY(Q+z2R>lYpoQs*o(4#3|#p^$PL3ZNPwoMwy~4Y-XUR22e>TvJS77P*XohBk=kTowQErXQAvM{tvbk;K97`3SYku
?ZPma`Et)nu@3gW#Utkm3B7s@N555>{cZJ&Fb)NnhvBk(`?)v_)PoLySlaFj?+>D{ML>nX=a>xv@N_(UOPD5Qu?%JPv%fG5E+u~r
Y=5>dc!%WwY7Ddi%Xi8lmEQFaQf4bt5@9%)ISwv0*ESy*XvDq_<LNNJLZM>*d=9#zojR)3*<w@!GAQ@z`UV1`w-5ZE(GEXa!{o6F
EJ^1I=&J~QI1l5kYhx>$F(Cg9F8a~{v=R~WI}UdKyk4e~pjt8t
""".replace("\n", ""))


def rol(x, n):
    x &= MASK
    n &= 63
    return ((x << n) | (x >> (64 - n))) & MASK if n else x & MASK


def mix(x):
    x &= MASK
    x ^= x >> 30
    x = x * 0xBF58476D1CE4E5B9 & MASK
    x ^= x >> 27
    x = x * 0x94D049BB133111EB & MASK
    return (x ^ (x >> 31)) & MASK


def zword(domain, index):
    return mix(0x6A09E667F3BCC909 ^ domain * 0x9E3779B97F4A7C15 ^
               (index + 0x100000001B3) * 0xBF58476D1CE4E5B9)


def info(board):
    occupied = white = black = h = 0
    signature = INITIAL[0]
    for square, piece in sorted(board.piece_map().items()):
        number = piece.piece_type + (0 if piece.color == chess.WHITE else 6)
        bit = 1 << square
        occupied |= bit
        white |= bit if piece.color == chess.WHITE else 0
        black |= bit if piece.color == chess.BLACK else 0
        h ^= zword(1, (number - 1) * 64 + square)
        signature = rol(signature + zword(5, number * 67 + square), 11)
    h ^= zword(2, 0) if board.turn == chess.BLACK else 0
    castle = (board.has_kingside_castling_rights(chess.WHITE) |
              board.has_queenside_castling_rights(chess.WHITE) << 1 |
              board.has_kingside_castling_rights(chess.BLACK) << 2 |
              board.has_queenside_castling_rights(chess.BLACK) << 3)
    h ^= zword(3, castle)
    ep = board.ep_square if board.ep_square is not None else 255
    h ^= zword(4, ep) if ep != 255 else 0
    return h & MASK, occupied, white, black, signature, castle, ep


def encode(board, move):
    if board.is_castling(move): kind = 3
    elif board.is_en_passant(move): kind = 4
    elif move.promotion:
        kind = 5 + (move.promotion - chess.KNIGHT) + (4 if board.is_capture(move) else 0)
    elif board.is_capture(move): kind = 1
    elif (board.piece_type_at(move.from_square) == chess.PAWN and
          abs(move.to_square - move.from_square) == 16): kind = 2
    else: kind = 0
    return kind << 12 | move.from_square << 6 | move.to_square


def decode_move(board, value):
    kind, source, target = value >> 12, value >> 6 & 63, value & 63
    promotion = (chess.KNIGHT + ((kind - 5) & 3)) if 5 <= kind <= 12 else None
    move = chess.Move(source, target, promotion=promotion)
    # The vendored chesslib's generator corresponds to python-chess's
    # pseudo-legal iterator on the long generated line.
    if move not in board.generate_pseudo_legal_moves() or encode(board, move) != value:
        raise ValueError(f"illegal recovered reply {value:04x}")
    return move


def targets():
    return [struct.unpack_from("<QH", TARGET_DATA, i * 10) for i in range(100)]


def recover_line():
    board, line = chess.Board(), []
    for wanted, reply in targets():
        matches = []
        for move in board.generate_pseudo_legal_moves():
            board.push(move)
            if info(board)[0] == wanted: matches.append(move)
            board.pop()
        if len(matches) != 1:
            raise ValueError(f"target {wanted:016x} has {len(matches)} legal predecessors")
        encoded = encode(board, matches[0])
        board.push(matches[0]); line.append(encoded)
        black = decode_move(board, reply)
        line.append(encode(board, black)); board.push(black)
    return line, board


def key_step(state, a, b, salt, board_info, ply):
    h, occupied, _, _, signature, _, _ = board_info
    x = (a ^ rol(b, salt) ^ h ^ ply * 0x9E3779B97F4A7C15) & MASK
    s0, s1, s2, s3 = state
    n0 = (s0 + mix(x ^ s2)) & MASK
    n1 = s1 ^ rol(s0, 17 + salt % 31)
    n2 = (s2 + (s1 ^ signature)) & MASK
    n3 = s3 ^ mix(s2 + occupied + x)
    return [rol(n0 ^ n3, 13), rol(n1 + n0, 29),
            rol(n2 ^ n1, 41), rol(n3 + n2, 7)]


def derive_key(with_trace=False):
    line, _ = recover_line()
    board, state, rows = chess.Board(), list(INITIAL), []
    for ply, value in enumerate(line):
        move = decode_move(board, value)
        board.push(move); board_info = info(board)
        state = key_step(state, value, board_info[0], 7, board_info, ply)
        if with_trace:
            rows.append({"ply": ply, "move": value, "uci": move.uci(),
                         "hash": board_info[0], "state": state.copy()})
    h, occupied, white, black, signature, castle, ep = board_info
    meta = occupied ^ rol(white, 7) ^ rol(black, 37) ^ signature
    meta ^= castle << 56 | ep << 40 | board.halfmove_clock << 16 | board.fullmove_number
    state = key_step(state, h, meta, 11, board_info, len(line))
    return b"".join(x.to_bytes(8, "little") for x in state), rows


def stream_xor(data, key, nonce):
    out = bytearray(data)
    for off in range(0, len(out), 32):
        block = hashlib.blake2s(nonce + struct.pack("<I", 1 + off // 32), key=key).digest()
        out[off:off + 32] = bytes(a ^ b for a, b in zip(out[off:off + 32], block))
    return bytes(out)


def decrypt(path):
    data = path.read_bytes()
    version, flags, length = struct.unpack_from("<HHI", data, 4)
    if data[:4] != b"BRSE" or version != 1 or flags or len(data) != 56 + length:
        raise ValueError("invalid BRSE container")
    master, _ = derive_key()
    enc = hashlib.blake2s(b"BRSE-ENC-v1", key=master).digest()
    mac = hashlib.blake2s(b"BRSE-MAC-v1", key=master).digest()
    if not hmac.compare_digest(hashlib.blake2s(data[:24 + length], key=mac).digest(), data[-32:]):
        raise ValueError("The rose withers.")
    return stream_xor(data[24:-32], enc, data[12:24])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path,
                        default=Path(__file__).resolve().parents[1] / "flag.enc")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--disassemble", action="store_true")
    args = parser.parse_args()
    line, _ = recover_line()
    print(f"Recovered {len(line)} half-moves:", " ".join(decode_uci(x) for x in line))
    if args.trace:
        key, rows = derive_key(True)
        for row in rows:
            print(f"{row['ply']:03d} {row['uci']:5s} hash={row['hash']:016x} state=" +
                  " ".join(f"{x:016x}" for x in row["state"]))
        print("derived key:", key.hex())
    if args.disassemble:
        from disassemble_vm import disassemble
        print("\n" + disassemble())
    print(decrypt(args.path).decode())


def decode_uci(value):
    source, target, kind = value >> 6 & 63, value & 63, value >> 12
    suffix = "nbrq"[(kind - 5) & 3] if 5 <= kind <= 12 else ""
    return chess.square_name(source) + chess.square_name(target) + suffix


if __name__ == "__main__":
    main()
