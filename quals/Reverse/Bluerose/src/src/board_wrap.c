#include "board_wrap.h"
#include "obfuscate.h"
#include "zobrist.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "chesslib/chess.h"

static chess *impl(const RoseBoard *board) {
    return (chess *)board->game;
}

static uint8_t move_kind_for(chess *g, move m) {
    board *b = chessGetBoard(g);
    const uint8_t from = sqGetIndex(m.from);
    const uint8_t to = sqGetIndex(m.to);
    const piece moving = boardGetPiece(b, m.from);
    const piece target = boardGetPiece(b, m.to);
    const int capture = target != pEmpty;

    if (m.promotion != ptEmpty) {
        uint8_t base = RM_PROMOTE_N;
        if (m.promotion == ptBishop) base = RM_PROMOTE_B;
        else if (m.promotion == ptRook) base = RM_PROMOTE_R;
        else if (m.promotion == ptQueen) base = RM_PROMOTE_Q;
        return (uint8_t)(base + (capture ? 4 : 0));
    }
    if (pieceGetType(moving) == ptKing &&
        (from > to ? from - to : to - from) == 2U) return RM_CASTLE;
    if (pieceGetType(moving) == ptPawn && target == pEmpty &&
        m.from.file != m.to.file) return RM_EN_PASSANT;
    if (pieceGetType(moving) == ptPawn &&
        (from > to ? from - to : to - from) == 16U) return RM_DOUBLE_PAWN;
    return capture ? RM_CAPTURE : RM_QUIET;
}

static RoseMove from_library_move(chess *g, move m) {
    return rose_encode_move(sqGetIndex(m.from), sqGetIndex(m.to), move_kind_for(g, m));
}

static pieceType promotion_for_kind(uint8_t kind) {
    if (kind == RM_PROMOTE_N || kind == RM_PROMOTE_CAPTURE_N) return ptKnight;
    if (kind == RM_PROMOTE_B || kind == RM_PROMOTE_CAPTURE_B) return ptBishop;
    if (kind == RM_PROMOTE_R || kind == RM_PROMOTE_CAPTURE_R) return ptRook;
    if (kind == RM_PROMOTE_Q || kind == RM_PROMOTE_CAPTURE_Q) return ptQueen;
    return ptEmpty;
}

static move to_library_move(RoseMove encoded) {
    const sq from = sqIndex(rose_move_from(encoded));
    const sq to = sqIndex(rose_move_to(encoded));
    const pieceType promotion = promotion_for_kind(rose_move_kind(encoded));
    return promotion == ptEmpty ? moveSq(from, to) : movePromote(from, to, promotion);
}

int rose_board_init(RoseBoard *board) {
    if (board == NULL) return 0;
    board->game = chessCreate();
    return board->game != NULL;
}

void rose_board_destroy(RoseBoard *board) {
    if (board != NULL && board->game != NULL) {
        chessFree(impl(board));
        board->game = NULL;
    }
}

int rose_board_reset(RoseBoard *board) {
    if (board == NULL) return 0;
    rose_board_destroy(board);
    return rose_board_init(board);
}

size_t rose_generate_legal_moves(const RoseBoard *board, RoseMove *out, size_t capacity) {
    if (board == NULL || board->game == NULL) return 0;
    moveList *list = chessGetLegalMoves(impl(board));
    size_t count = 0;
    for (moveListNode *node = list->head; node != NULL; node = node->next) {
        if (out != NULL && count < capacity) out[count] = from_library_move(impl(board), node->move);
        count++;
    }
    return count;
}

int rose_apply_move(RoseBoard *board, RoseMove encoded) {
    if (board == NULL || board->game == NULL) return 0;
    return chessPlayMove(impl(board), to_library_move(encoded)) == 0;
}

int rose_move_is_legal(const RoseBoard *board, RoseMove encoded) {
    RoseMove moves[256];
    const size_t count = rose_generate_legal_moves(board, moves, 256);
    for (size_t i = 0; i < count && i < 256; i++) {
        if (moves[i] == encoded) return 1;
    }
    return 0;
}

uint8_t rose_piece_at(const RoseBoard *board, uint8_t square) {
    if (board == NULL || board->game == NULL || square >= 64) return 0;
    return (uint8_t)chessGetPiece(impl(board), sqIndex(square));
}

enum RoseSide rose_side_to_move(const RoseBoard *board) {
    return chessGetPlayer(impl(board)) == pcBlack ? ROSE_BLACK : ROSE_WHITE;
}

enum RoseGameStatus rose_game_status(const RoseBoard *board) {
    switch (chessGetTerminalState(impl(board))) {
        case tsOngoing: return ROSE_PLAYING;
        case tsCheckmate: return ROSE_CHECKMATE;
        case tsDrawStalemate: return ROSE_STALEMATE;
        default: return ROSE_DRAW;
    }
}

int rose_is_in_check(const RoseBoard *board) {
    return chessIsInCheck(impl(board)) != 0;
}

ROSE_OBF_ARITH void rose_position_info(const RoseBoard *board, RosePositionInfo *out) {
    memset(out, 0, sizeof *out);
    chess *g = impl(board);
    uint64_t hash = 0;
    uint64_t signature = UINT64_C(0x243f6a8885a308d3);
    for (uint8_t square = 0; square < 64; square++) {
        const uint8_t p = (uint8_t)chessGetPiece(g, sqIndex(square));
        if (p == pEmpty) continue;
        const uint64_t bit = UINT64_C(1) << square;
        out->occupied |= bit;
        if (pieceGetColor((piece)p) == pcWhite) out->white_occupied |= bit;
        else out->black_occupied |= bit;
        hash ^= rose_zobrist_word(1, (uint64_t)(p - 1U) * 64U + square);
        signature += rose_zobrist_word(5, (uint64_t)p * 67U + square);
        signature = (signature << 11) | (signature >> 53);
    }
    out->side_to_move = chessGetPlayer(g) == pcBlack ? ROSE_BLACK : ROSE_WHITE;
    out->castling = chessGetCastleState(g) & 0x0fU;
    const sq ep = chessGetEpTarget(g);
    out->ep_square = (ep.file >= 1 && ep.file <= 8 && ep.rank >= 1 && ep.rank <= 8)
                         ? sqGetIndex(ep) : 0xffU;
    out->halfmove_clock = (uint16_t)chessGetHalfMoveClock(g);
    out->fullmove_number = (uint16_t)chessGetMoveNumber(g);
    if (out->side_to_move == ROSE_BLACK) hash ^= rose_zobrist_word(2, 0);
    hash ^= rose_zobrist_word(3, out->castling);
    if (out->ep_square != 0xffU) hash ^= rose_zobrist_word(4, out->ep_square);
    out->hash = hash;
    out->piece_signature = signature;
}

ROSE_OBF_ARITH uint64_t rose_position_hash(const RoseBoard *board) {
    RosePositionInfo info;
    rose_position_info(board, &info);
    return info.hash;
}

void rose_format_move(RoseMove move_value, char out[8]) {
    const uint8_t from = rose_move_from(move_value);
    const uint8_t to = rose_move_to(move_value);
    out[0] = (char)('a' + from % 8U);
    out[1] = (char)('1' + from / 8U);
    out[2] = (rose_move_kind(move_value) == RM_CAPTURE ||
              rose_move_kind(move_value) == RM_EN_PASSANT ||
              rose_move_kind(move_value) >= RM_PROMOTE_CAPTURE_N) ? 'x' : '-';
    out[3] = (char)('a' + to % 8U);
    out[4] = (char)('1' + to / 8U);
    out[5] = '\0';
}

int rose_move_tactical_score(const RoseBoard *wrapped, RoseMove encoded) {
    static const int values[] = {0, 100, 320, 330, 500, 900, 20000};
    chess *g = impl(wrapped);
    board *before = chessGetBoard(g);
    const move m = to_library_move(encoded);
    int score = 0;
    const piece victim = boardGetPiece(before, m.to);
    if (victim != pEmpty) score += values[pieceGetType(victim)] * 16;
    if (rose_move_kind(encoded) == RM_EN_PASSANT) score += 1600;
    if (m.promotion != ptEmpty) score += values[m.promotion] * 8;

    board *after = boardPlayMove(before, m);
    if (after == NULL) return score;
    const int gives_check = boardIsInCheck(after) != 0;
    if (gives_check) score += 700;
    moveList *reply = boardGenerateMoves(after);
    if (reply != NULL && reply->size == 0 && gives_check) score += 1000000;
    moveListFree(reply);
    free(after);

    const uint8_t to = rose_move_to(encoded);
    const int file = (int)(to % 8U);
    const int rank = (int)(to / 8U);
    score += 24 - 4 * (abs(file - 3) + abs(rank - 3));
    const uint8_t from = rose_move_from(encoded);
    if (from == 57U || from == 62U || from == 58U || from == 61U) score += 80;
    return score;
}
