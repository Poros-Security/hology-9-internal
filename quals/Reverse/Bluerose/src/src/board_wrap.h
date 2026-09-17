#ifndef BLUEROSE_BOARD_WRAP_H
#define BLUEROSE_BOARD_WRAP_H

#include <stddef.h>
#include <stdint.h>

typedef uint16_t RoseMove;

enum RoseMoveKind {
    RM_QUIET = 0,
    RM_CAPTURE = 1,
    RM_DOUBLE_PAWN = 2,
    RM_CASTLE = 3,
    RM_EN_PASSANT = 4,
    RM_PROMOTE_N = 5,
    RM_PROMOTE_B = 6,
    RM_PROMOTE_R = 7,
    RM_PROMOTE_Q = 8,
    RM_PROMOTE_CAPTURE_N = 9,
    RM_PROMOTE_CAPTURE_B = 10,
    RM_PROMOTE_CAPTURE_R = 11,
    RM_PROMOTE_CAPTURE_Q = 12
};

enum RoseSide {
    ROSE_WHITE = 0,
    ROSE_BLACK = 1
};

enum RoseGameStatus {
    ROSE_PLAYING = 0,
    ROSE_CHECKMATE,
    ROSE_STALEMATE,
    ROSE_DRAW
};

typedef struct {
    void *game;
} RoseBoard;

typedef struct {
    uint64_t hash;
    uint64_t occupied;
    uint64_t white_occupied;
    uint64_t black_occupied;
    uint64_t piece_signature;
    uint8_t side_to_move;
    uint8_t castling;
    uint8_t ep_square;
    uint16_t halfmove_clock;
    uint16_t fullmove_number;
} RosePositionInfo;

static inline RoseMove rose_encode_move(uint8_t from, uint8_t to, uint8_t kind) {
    return (RoseMove)(((uint16_t)(kind & 0x0fU) << 12) |
                      ((uint16_t)(from & 0x3fU) << 6) |
                      (uint16_t)(to & 0x3fU));
}

static inline uint8_t rose_move_to(RoseMove m) { return (uint8_t)(m & 0x3fU); }
static inline uint8_t rose_move_from(RoseMove m) { return (uint8_t)((m >> 6) & 0x3fU); }
static inline uint8_t rose_move_kind(RoseMove m) { return (uint8_t)((m >> 12) & 0x0fU); }

int rose_board_init(RoseBoard *board);
void rose_board_destroy(RoseBoard *board);
int rose_board_reset(RoseBoard *board);
size_t rose_generate_legal_moves(const RoseBoard *board, RoseMove *out, size_t capacity);
int rose_apply_move(RoseBoard *board, RoseMove move);
int rose_move_is_legal(const RoseBoard *board, RoseMove move);
uint8_t rose_piece_at(const RoseBoard *board, uint8_t square);
enum RoseSide rose_side_to_move(const RoseBoard *board);
enum RoseGameStatus rose_game_status(const RoseBoard *board);
int rose_is_in_check(const RoseBoard *board);
void rose_position_info(const RoseBoard *board, RosePositionInfo *out);
uint64_t rose_position_hash(const RoseBoard *board);
void rose_format_move(RoseMove move, char out[8]);
int rose_move_tactical_score(const RoseBoard *board, RoseMove move);

#endif
