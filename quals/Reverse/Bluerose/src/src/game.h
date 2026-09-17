#ifndef BLUEROSE_GAME_H
#define BLUEROSE_GAME_H

#include <stddef.h>
#include <stdint.h>

#include "board_wrap.h"
#include "rosevm.h"

typedef struct {
    RoseBoard board;
    RoseVm vm;
    RoseMove history[256];
    size_t history_count;
    char message[160];
    char revealed[512];
    uint64_t debug_word;
    uint8_t complete;
    uint8_t bloomed;
} RoseGame;

int rose_game_init(RoseGame *game);
void rose_game_destroy(RoseGame *game);
int rose_game_restart(RoseGame *game);
int rose_game_player_move(RoseGame *game, uint8_t from, uint8_t to);
int rose_game_bot_move(RoseGame *game);
size_t rose_game_legal_from(const RoseGame *game, uint8_t from, RoseMove *out, size_t capacity);

#endif
