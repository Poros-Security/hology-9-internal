

#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>

typedef struct Card {
    char      msg[64];             
    uint64_t  view_count;        
    void    (*formatter)(struct Card *); 
} Card;


__attribute__((constructor))
static void _unbuffer(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
}


void default_formatter(Card *card) {
    card->view_count++;
    printf("+----------------------------------------------------------------+\n");
    printf("| %-62.62s |\n", card->msg);
    printf("+----------------------------------------------------------------+\n");
    printf("| views: %-55llu |\n", (unsigned long long)card->view_count);
    printf("+----------------------------------------------------------------+\n");
}


void get_flag(Card *card) {
    (void)card;
    char buf[128];
    FILE *f = fopen("flag.txt", "r");
    if (!f) {
        puts("flag.txt missing -- ask the organizers.");
        return;
    }
    if (fgets(buf, sizeof(buf), f)) {
        printf("%s", buf);
    }
    fclose(f);
}

void init_card(Card *card) {
    memset(card->msg, 0, sizeof(card->msg));
    card->view_count = 0;
    card->formatter  = default_formatter;
}


void load_card(Card *card, const uint8_t *src, size_t len) {
    memcpy(card->msg, src, len);
}

void render_card(Card *card) {
    card->formatter(card);
}
