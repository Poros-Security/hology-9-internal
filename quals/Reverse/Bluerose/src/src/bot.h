#ifndef BLUEROSE_BOT_H
#define BLUEROSE_BOT_H

#include "board_wrap.h"

#define ROSE_PATH_ROUNDS 100U

RoseMove rose_bot_choose(const RoseBoard *board, int *used_hidden_reply);
int rose_bot_decode_entry(unsigned index, uint64_t *hash, RoseMove *move);

#endif
