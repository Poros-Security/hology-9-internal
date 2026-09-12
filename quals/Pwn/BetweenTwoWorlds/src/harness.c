
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>

typedef struct Card {
    char      msg[64];
    uint64_t  view_count;
    void    (*formatter)(struct Card *);
} Card;

void init_card(Card *);
void load_card(Card *, const uint8_t *, size_t);
void render_card(Card *);
void get_flag(Card *);  

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);

    puts("==================== SafeNotes v1.0 ====================");
    puts(" Memory-safe notes, powered by Rust. Native rendering by");
    puts(" libnotes (C). Paste your note and press Ctrl-D.");
    puts("========================================================");


    Card card;
    init_card(&card);


    static uint8_t note[256];
    ssize_t n = fread(note, 1, sizeof(note), stdin);
    if (n < 0) return 1;

    load_card(&card, note, (size_t)n);

    render_card(&card);
    return 0;
}
