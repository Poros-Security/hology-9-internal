/*
 * mallet -- the Whack a Mole minigame.
 *
 * Digs holes. Shows you what came up. Says nothing about whether it was any
 * good, because it genuinely does not know: there is no table of right
 * answers in here, only a seed, a salt and two mixing functions.
 */
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "molecrypt.h"

static uint8_t holes[NUM_HOLES][HOLE_SIZE];
static char    dug[NUM_HOLES];

static void load_holes(void)
{
    int i;

    for (i = 0; i < NUM_HOLES; i++) {
        char path[64];
        FILE *f;

        snprintf(path, sizeof(path), "holes/hole_%02d.bin", i);
        f = fopen(path, "rb");
        if (!f) {
            fprintf(stderr, "mallet: cannot open %s\n", path);
            exit(1);
        }
        if (fread(holes[i], 1, HOLE_SIZE, f) != HOLE_SIZE) {
            fprintf(stderr, "mallet: %s is not %d bytes\n", path, HOLE_SIZE);
            fclose(f);
            exit(1);
        }
        fclose(f);
    }
}

static void banner(void)
{
    puts("");
    puts("  =============================================");
    puts("   W H A C K   A   M O L E");
    puts("  =============================================");
    puts("   Ten by ten. One hundred holes.");
    puts("   You get 12 swings. Dig, and see what's down there.");
    puts("");
    puts("   Coordinates: 'C7' (column A-J, row 0-9) or '7,2' (row,col).");
    puts("");
}

static void draw_grid(void)
{
    int r, c;

    puts("       A  B  C  D  E  F  G  H  I  J");
    puts("    +-------------------------------+");
    for (r = 0; r < GRID; r++) {
        printf("  %d |", r);
        for (c = 0; c < GRID; c++)
            printf("  %c", dug[r * GRID + c] ? 'x' : '.');
        puts(" |");
    }
    puts("    +-------------------------------+");
    puts("");
}

static void hexdump(const uint8_t *buf, size_t n)
{
    size_t i, j;

    puts("       00 01 02 03 04 05 06 07  08 09 0a 0b 0c 0d 0e 0f");
    puts("       ------------------------------------------------   ----------------");
    for (i = 0; i < n; i += 16) {
        printf("  %03zx  ", i);
        for (j = 0; j < 16; j++) {
            if (i + j < n)
                printf("%02x ", buf[i + j]);
            else
                printf("   ");
            if (j == 7)
                putchar(' ');
        }
        printf(" |");
        for (j = 0; j < 16 && i + j < n; j++) {
            int ch = buf[i + j];
            putchar(isprint(ch) ? ch : '.');
        }
        puts("|");
    }
    puts("");
}

/* Column A-J plus row 0-9, or "row,col". Returns -1 on anything else. */
static int parse_pick(const char *line)
{
    int row = -1, col = -1;
    const char *p = line;

    while (*p == ' ' || *p == '\t')
        p++;

    if (strchr(p, ',')) {
        char *end;
        long a, b;

        a = strtol(p, &end, 10);
        if (end == p || *end != ',')
            return -1;
        p = end + 1;
        b = strtol(p, &end, 10);
        if (end == p)
            return -1;
        while (*end == ' ' || *end == '\t' || *end == '\r' || *end == '\n')
            end++;
        if (*end != '\0')
            return -1;
        row = (int)a;
        col = (int)b;
    } else {
        if (!isalpha((unsigned char)p[0]) || !isdigit((unsigned char)p[1]))
            return -1;
        col = toupper((unsigned char)p[0]) - 'A';
        row = p[1] - '0';
        p += 2;
        while (*p == ' ' || *p == '\t' || *p == '\r' || *p == '\n')
            p++;
        if (*p != '\0')
            return -1;
    }

    if (row < 0 || row >= GRID || col < 0 || col >= GRID)
        return -1;
    return row * GRID + col;
}

/* Blocks until a coordinate is in range. A bad coordinate never burns a round. */
static int prompt_pick(void)
{
    char line[128];

    for (;;) {
        int pick;

        printf("  dig> ");
        fflush(stdout);
        if (!fgets(line, sizeof(line), stdin)) {
            puts("");
            fprintf(stderr, "mallet: out of input\n");
            exit(1);
        }
        pick = parse_pick(line);
        if (pick >= 0)
            return pick;
        puts("  That's not on the field.");
    }
}

static void print_haul(const uint8_t *haul, size_t n)
{
    size_t i;

    printf("Your haul: ");
    for (i = 0; i < n; i++) {
        int ch = haul[i];
        if (isprint(ch))
            putchar(ch);
        else
            printf("\\x%02x", ch);
    }
    puts("");
}

int main(void)
{
    uint8_t haul[PATH_LEN * HOLE_SIZE];
    size_t haul_len = 0;
    uint64_t state = MOLE_SEED;
    int r;

    setvbuf(stdout, NULL, _IONBF, 0);
    load_holes();
    banner();
    draw_grid();

    for (r = 0; r < PATH_LEN; r++) {
        uint8_t plain[HOLE_SIZE];
        int pick, frag_len;

        printf("  Round %d/%d\n", r + 1, PATH_LEN);
        pick = prompt_pick();

        mole_crypt(holes[pick], plain, HOLE_SIZE, state, (uint8_t)pick);

        printf("\n  You dig at %c%d (hole %02d) and pull up:\n\n",
               'A' + (pick % GRID), pick / GRID, pick);
        hexdump(plain, HOLE_SIZE);

        /* Trust the length byte, clamp to the buffer. No magic check: the
         * binary has no idea what a correct hole looks like. */
        frag_len = plain[OFF_FRAGLEN];
        if (OFF_FRAG + frag_len > HOLE_SIZE)
            frag_len = HOLE_SIZE - OFF_FRAG;
        memcpy(haul + haul_len, plain + OFF_FRAG, (size_t)frag_len);
        haul_len += (size_t)frag_len;

        state = mole_advance(state, (uint8_t)pick, plain, HOLE_SIZE);

        dug[pick] = 1;
        draw_grid();
    }

    puts("  Twelve swings, and that's the lot.");
    puts("");
    print_haul(haul, haul_len);
    return 0;
}
