/*
 * Hallmark · pre-emit critique: P5 H5 E4 S5 R5 V5
 * genre: atmospheric · tone: restrained forensic · anchor: cobalt
 * macrostructure: fixed chess workbench + instrument rail · slop: pass
 */
#include "gui.h"

#include "game.h"

#include <raylib.h>

#include <math.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

#include "pieces_png.h"

enum {
    WINDOW_W = 1000,
    WINDOW_H = 720,
    BOARD_X = 32,
    BOARD_Y = 40,
    CELL = 80,
    BOARD_SIZE = CELL * 8,
    PANEL_X = 704,
    PANEL_W = 264
};

typedef struct {
    RoseGame game;
    int selected;
    RoseMove legal[32];
    size_t legal_count;
    int bot_pending;
    double bot_at;
} GuiState;

static const Color INK = {220, 231, 246, 255};
static const Color MUTED = {132, 151, 180, 255};
static const Color NIGHT = {7, 13, 28, 255};
static const Color PANEL = {12, 23, 46, 255};
static const Color PANEL_LINE = {36, 62, 99, 255};
static const Color LIGHT_SQ = {156, 178, 205, 255};
static const Color DARK_SQ = {42, 70, 111, 255};
static const Color COBALT = {54, 117, 219, 255};
static const Color CYAN = {92, 207, 235, 255};
static const Color ROSE_GOLD = {221, 178, 88, 255};
static const Color BOARD_FRAME = {19, 38, 68, 255};
static const Color BUTTON = {24, 48, 84, 255};
static const Color BUTTON_HOVER = {36, 78, 134, 255};
static const Color BUTTON_ACTIVE = {28, 63, 111, 255};
static const Color TURN_WELL = {8, 18, 37, 255};
static const Color BACKGROUND_BLOOM = {17, 40, 78, 100};
static Texture2D piece_sheet;

static Rectangle square_rect(uint8_t square) {
    const int file = square & 7U;
    const int rank = square >> 3;
    return (Rectangle){(float)(BOARD_X + file * CELL),
                       (float)(BOARD_Y + (7 - rank) * CELL), CELL, CELL};
}

static int screen_square(Vector2 point) {
    if (point.x < BOARD_X || point.y < BOARD_Y ||
        point.x >= BOARD_X + BOARD_SIZE || point.y >= BOARD_Y + BOARD_SIZE) return -1;
    const int file = ((int)point.x - BOARD_X) / CELL;
    const int screen_rank = ((int)point.y - BOARD_Y) / CELL;
    return (7 - screen_rank) * 8 + file;
}

static void draw_rose(Vector2 center, float radius, Color color) {
    for (int i = 0; i < 8; i++) {
        const float angle = (float)i * (2.0f * PI / 8.0f);
        const Vector2 petal = {center.x + cosf(angle) * radius * 0.48f,
                               center.y + sinf(angle) * radius * 0.48f};
        DrawCircleV(petal, radius * 0.36f, Fade(color, 0.46f));
    }
    DrawCircleV(center, radius * 0.32f, color);
    DrawCircleLines((int)center.x, (int)center.y, radius, Fade(CYAN, 0.5f));
}

static void draw_wrapped(const char *text, int x, int y, int max_width, int size,
                         int line_gap, Color color) {
    char line[192];
    size_t used = 0;
    const char *cursor = text;
    while (*cursor != '\0') {
        size_t take = 0, last_space = 0;
        while (cursor[take] != '\0' && take + 1U < sizeof line) {
            line[take] = cursor[take];
            line[take + 1U] = '\0';
            if (cursor[take] == ' ') last_space = take;
            if (MeasureText(line, size) > max_width) break;
            take++;
        }
        if (cursor[take] != '\0' && last_space != 0U) take = last_space;
        if (take == 0U) take = 1U;
        used = take;
        while (used > 0U && cursor[used - 1U] == ' ') used--;
        for (size_t i = 0; i < used; i++) line[i] = cursor[i];
        line[used] = '\0';
        DrawText(line, x, y, size, color);
        y += size + line_gap;
        cursor += take;
        while (*cursor == ' ') cursor++;
    }
}

static void draw_piece(uint8_t piece, Rectangle cell) {
    if (piece == 0U) return;
    const int white = piece <= 6U;
    const unsigned kind = ((unsigned)piece - 1U) % 6U + 1U;
    static const uint8_t sprite_column[6] = {5, 3, 2, 4, 1, 0};
    const Rectangle source = {(float)sprite_column[kind - 1U] * 128.0f,
                              white ? 0.0f : 128.0f, 128.0f, 128.0f};
    const Rectangle destination = {cell.x + 3.0f, cell.y + 3.0f,
                                   cell.width - 6.0f, cell.height - 6.0f};
    DrawTexturePro(piece_sheet, source, destination, (Vector2){0, 0}, 0.0f, WHITE);
}

static int destination_is_legal(const GuiState *ui, int square) {
    for (size_t i = 0; i < ui->legal_count; i++)
        if (rose_move_to(ui->legal[i]) == square) return 1;
    return 0;
}

static void draw_board(const GuiState *ui) {
    DrawRectangle(BOARD_X - 5, BOARD_Y - 5, BOARD_SIZE + 10, BOARD_SIZE + 10,
                  BOARD_FRAME);
    for (uint8_t square = 0; square < 64; square++) {
        const int file = square & 7U;
        const int rank = square >> 3;
        const Rectangle cell = square_rect(square);
        DrawRectangleRec(cell, ((file + rank) & 1) ? LIGHT_SQ : DARK_SQ);
        if (ui->selected == square) DrawRectangleRec(cell, Fade(ROSE_GOLD, 0.58f));
        if (destination_is_legal(ui, square)) {
            if (rose_piece_at(&ui->game.board, square) != 0U)
                DrawRectangleLinesEx((Rectangle){cell.x + 5, cell.y + 5, cell.width - 10,
                                                  cell.height - 10}, 4, Fade(CYAN, 0.85f));
            else
                DrawCircle((int)(cell.x + CELL / 2), (int)(cell.y + CELL / 2), 10,
                           Fade(CYAN, 0.70f));
        }
        draw_piece(rose_piece_at(&ui->game.board, square), cell);
    }

    for (int i = 0; i < 8; i++) {
        char file[2] = {(char)('a' + i), '\0'};
        char rank[2] = {(char)('8' - i), '\0'};
        DrawText(file, BOARD_X + i * CELL + 5, BOARD_Y + BOARD_SIZE - 17, 13,
                 (i & 1) ? DARK_SQ : LIGHT_SQ);
        DrawText(rank, BOARD_X + 4, BOARD_Y + i * CELL + 4, 13,
                 (i & 1) ? LIGHT_SQ : DARK_SQ);
    }
}

static void draw_history(const GuiState *ui) {
    DrawText("MOVE LOG", PANEL_X + 18, 174, 12, MUTED);
    DrawLine(PANEL_X + 18, 194, PANEL_X + PANEL_W - 18, 194, PANEL_LINE);
    const size_t rounds = (ui->game.history_count + 1U) / 2U;
    const size_t visible = rounds > 13U ? 13U : rounds;
    const size_t start = rounds - visible;
    for (size_t row = 0; row < visible; row++) {
        const size_t round = start + row;
        char number[12];
        char white[8] = "";
        char black[8] = "";
        snprintf(number, sizeof number, "%2zu", round + 1U);
        rose_format_move(ui->game.history[round * 2U], white);
        if (round * 2U + 1U < ui->game.history_count)
            rose_format_move(ui->game.history[round * 2U + 1U], black);
        const int y = 207 + (int)row * 25;
        DrawText(number, PANEL_X + 18, y, 16, MUTED);
        DrawText(white, PANEL_X + 54, y, 16, INK);
        DrawText(black, PANEL_X + 147, y, 16, INK);
    }
    if (rounds == 0U) DrawText("No movements yet.", PANEL_X + 18, 210, 16, MUTED);
}

static int button(Rectangle rect, const char *label) {
    const Vector2 mouse = GetMousePosition();
    const int hover = CheckCollisionPointRec(mouse, rect);
    const int held = hover && IsMouseButtonDown(MOUSE_BUTTON_LEFT);
    DrawRectangleRounded(rect, 0.12f, 6, held ? BUTTON_ACTIVE : hover ? BUTTON_HOVER : BUTTON);
    DrawRectangleRoundedLinesEx(rect, 0.12f, 6, 1, hover ? CYAN : PANEL_LINE);
    const int width = MeasureText(label, 17);
    DrawText(label, (int)(rect.x + (rect.width - width) / 2), (int)rect.y + 12, 17, INK);
    return hover && IsMouseButtonPressed(MOUSE_BUTTON_LEFT);
}

static void draw_panel(const GuiState *ui) {
    DrawRectangle(PANEL_X, 0, WINDOW_W - PANEL_X, WINDOW_H, PANEL);
    DrawLine(PANEL_X, 0, PANEL_X, WINDOW_H, PANEL_LINE);
    draw_rose((Vector2){PANEL_X + 36, 50}, 20, COBALT);
    DrawText("BLUEROSE", PANEL_X + 68, 29, 27, INK);
    

    DrawRectangleRounded((Rectangle){PANEL_X + 18, 112, PANEL_W - 36, 43}, 0.12f, 6,
                         TURN_WELL);
    DrawCircle(PANEL_X + 36, 133, 5,
               rose_side_to_move(&ui->game.board) == ROSE_WHITE ? INK : COBALT);
    DrawText(ui->game.complete ? "GAME COMPLETE" :
             (rose_side_to_move(&ui->game.board) == ROSE_WHITE ? "WHITE TO MOVE" : "BLACK IS THINKING"),
             PANEL_X + 50, 125, 15, INK);

    draw_history(ui);
    DrawLine(PANEL_X + 18, 545, PANEL_X + PANEL_W - 18, 545, PANEL_LINE);
    DrawText("STATUS", PANEL_X + 18, 560, 12, MUTED);
    draw_wrapped(ui->game.message, PANEL_X + 18, 582, PANEL_W - 36, 16, 3,
                 ui->game.bloomed ? CYAN : INK);
}

static void draw_bloom_overlay(const GuiState *ui) {
    if (!ui->game.bloomed) return;

    const Rectangle card = {BOARD_X + 52, BOARD_Y + 218, BOARD_SIZE - 104, 204};
    DrawRectangleRounded(card, 0.08f, 10, Fade(PANEL, 0.97f));
    DrawRectangleRoundedLinesEx(card, 0.08f, 10, 2.0f, CYAN);
    draw_rose((Vector2){card.x + 38.0f, card.y + 38.0f}, 16.0f, COBALT);
    DrawText("A BLUE ROSE BLOOMS", (int)card.x + 67, (int)card.y + 24, 22, INK);
    DrawLine((int)card.x + 22, (int)card.y + 69,
             (int)(card.x + card.width) - 22, (int)card.y + 69, PANEL_LINE);
    draw_wrapped(ui->game.revealed, (int)card.x + 25, (int)card.y + 91,
                 (int)card.width - 50, 18, 8, CYAN);
}

static void clear_selection(GuiState *ui) {
    ui->selected = -1;
    ui->legal_count = 0;
}

static void handle_board_click(GuiState *ui) {
    if (!IsMouseButtonPressed(MOUSE_BUTTON_LEFT) || ui->bot_pending || ui->game.complete ||
        rose_side_to_move(&ui->game.board) != ROSE_WHITE) return;
    const int square = screen_square(GetMousePosition());
    if (square < 0) return;
    if (ui->selected >= 0 && destination_is_legal(ui, square)) {
        if (rose_game_player_move(&ui->game, (uint8_t)ui->selected, (uint8_t)square) &&
            !ui->game.complete && rose_side_to_move(&ui->game.board) == ROSE_BLACK) {
            ui->bot_pending = 1;
            ui->bot_at = GetTime() + 0.28;
        }
        clear_selection(ui);
        return;
    }
    const uint8_t piece = rose_piece_at(&ui->game.board, (uint8_t)square);
    if (piece >= 1U && piece <= 6U) {
        ui->selected = square;
        ui->legal_count = rose_game_legal_from(&ui->game, (uint8_t)square, ui->legal, 32);
    } else {
        clear_selection(ui);
    }
}

int rose_gui_run(void) {
    GuiState ui = {.selected = -1};
    InitWindow(WINDOW_W, WINDOW_H, "Bluerose");
    Image pieces = LoadImageFromMemory(".png", rose_piece_png, (int)rose_piece_png_len);
    piece_sheet = LoadTextureFromImage(pieces);
    UnloadImage(pieces);
    SetTargetFPS(60);
    if (!rose_game_init(&ui.game)) {
        CloseWindow();
        return 1;
    }

    while (!WindowShouldClose()) {
        handle_board_click(&ui);
        if (ui.bot_pending && GetTime() >= ui.bot_at) {
            (void)rose_game_bot_move(&ui.game);
            ui.bot_pending = 0;
        }
        const Rectangle restart = {(float)PANEL_X + 18, 654, (float)PANEL_W - 36, 46};

        BeginDrawing();
        ClearBackground(NIGHT);
        DrawCircleGradient((Vector2){170, 90}, 310, BACKGROUND_BLOOM, NIGHT);
        draw_board(&ui);
        draw_panel(&ui);
        draw_bloom_overlay(&ui);
        const int restart_clicked = button(restart, "RESTART GAME");
        EndDrawing();

        if (restart_clicked) {
            (void)rose_game_restart(&ui.game);
            ui.bot_pending = 0;
            clear_selection(&ui);
        }
    }
    rose_game_destroy(&ui.game);
    UnloadTexture(piece_sheet);
    CloseWindow();
    return 0;
}
