#include "game.h"

#include "antidebug.h"
#include "bot.h"
#include "crypto.h"
#include "flagfile.h"

#include <stdio.h>
#include <string.h>

static void update_status(RoseGame *game) {
    const enum RoseGameStatus state = rose_game_status(&game->board);
    if (game->complete) return;
    if (state == ROSE_PLAYING) {
        if (rose_is_in_check(&game->board))
            snprintf(game->message, sizeof game->message, "%s is in check.",
                     rose_side_to_move(&game->board) == ROSE_WHITE ? "White" : "Black");
        else
            snprintf(game->message, sizeof game->message, "%s to move.",
                     rose_side_to_move(&game->board) == ROSE_WHITE ? "White" : "Black");
    } else if (state == ROSE_CHECKMATE) {
        snprintf(game->message, sizeof game->message, "Checkmate.");
    } else if (state == ROSE_STALEMATE) {
        snprintf(game->message, sizeof game->message, "Stalemate.");
    } else {
        snprintf(game->message, sizeof game->message, "The game is drawn.");
    }
}

static int record_halfmove(RoseGame *game, RoseMove move_value) {
    if (game->history_count >= sizeof game->history / sizeof game->history[0]) return 0;
    RosePositionInfo position;
    rose_position_info(&game->board, &position);
    const uint16_t ply = (uint16_t)game->history_count;
    game->history[game->history_count++] = move_value;
    return rosevm_step(&game->vm, move_value, &position, ply);
}

static void open_at_end(RoseGame *game) {
    const int terminal = rose_game_status(&game->board) != ROSE_PLAYING;
    if (game->complete || (!terminal && game->history_count < ROSE_PATH_ROUNDS * 2U)) return;
    RosePositionInfo final_position;
    uint8_t master[32];
    rose_position_info(&game->board, &final_position);
    game->complete = 1;
    if (rosevm_finish(&game->vm, &final_position, (uint16_t)game->history_count, master) &&
        rose_flag_open("flag.enc", master, game->revealed, sizeof game->revealed)) {
        game->bloomed = 1;
        snprintf(game->message, sizeof game->message,
                 "A blue rose blooms where none should grow.");
    } else {
        game->bloomed = 0;
        game->revealed[0] = '\0';
        snprintf(game->message, sizeof game->message, "The rose withers.");
    }
    rose_burn(master, sizeof master);
}

int rose_game_init(RoseGame *game) {
    memset(game, 0, sizeof *game);
    if (!rosevm_global_init() || !rose_board_init(&game->board)) return 0;
    game->debug_word = rose_debug_word();
    if (!rosevm_reset(&game->vm, game->debug_word)) {
        rose_board_destroy(&game->board);
        return 0;
    }
    update_status(game);
    return 1;
}

void rose_game_destroy(RoseGame *game) {
    rose_board_destroy(&game->board);
    rose_burn(&game->vm, sizeof game->vm);
}

int rose_game_restart(RoseGame *game) {
    if (!rose_board_reset(&game->board)) return 0;
    game->history_count = 0;
    game->complete = 0;
    game->bloomed = 0;
    game->revealed[0] = '\0';
    game->debug_word = rose_debug_word();
    if (!rosevm_reset(&game->vm, game->debug_word)) return 0;
    update_status(game);
    return 1;
}

size_t rose_game_legal_from(const RoseGame *game, uint8_t from, RoseMove *out, size_t capacity) {
    RoseMove all[256];
    const size_t count = rose_generate_legal_moves(&game->board, all, 256);
    size_t selected = 0;
    for (size_t i = 0; i < count && i < 256; i++) {
        if (rose_move_from(all[i]) == from) {
            if (out != NULL && selected < capacity) out[selected] = all[i];
            selected++;
        }
    }
    return selected;
}

int rose_game_player_move(RoseGame *game, uint8_t from, uint8_t to) {
    if (game->complete || rose_game_status(&game->board) != ROSE_PLAYING ||
        rose_side_to_move(&game->board) != ROSE_WHITE) return 0;
    RoseMove candidates[32];
    const size_t count = rose_game_legal_from(game, from, candidates, 32);
    RoseMove choice = 0;
    for (size_t i = 0; i < count && i < 32; i++) {
        if (rose_move_to(candidates[i]) != to) continue;
        choice = candidates[i];
        if (rose_move_kind(choice) == RM_PROMOTE_Q ||
            rose_move_kind(choice) == RM_PROMOTE_CAPTURE_Q) break;
    }
    if (choice == 0 || !rose_apply_move(&game->board, choice)) return 0;
    if (!record_halfmove(game, choice)) return 0;
    update_status(game);
    open_at_end(game);
    return 1;
}

int rose_game_bot_move(RoseGame *game) {
    if (game->complete || rose_game_status(&game->board) != ROSE_PLAYING ||
        rose_side_to_move(&game->board) != ROSE_BLACK) return 0;
    int hidden_reply = 0;
    const RoseMove move_value = rose_bot_choose(&game->board, &hidden_reply);
    (void)hidden_reply;
    if (move_value == 0 || !rose_apply_move(&game->board, move_value)) return 0;
    if (!record_halfmove(game, move_value)) return 0;
    update_status(game);
    open_at_end(game);
    return 1;
}
