#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

static void setup(void) {
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
}

void win(void) {
    FILE *f = fopen("/tmp/flag.txt", "r");
    char flag[128] = {0};

    if (!f) {
        puts("flag.txt missing");
        exit(1);
    }

    fgets(flag, sizeof(flag), f);
    fclose(f);

    printf("[win] %s", flag);
    exit(0);
}

static void banner(void) {
    puts("A million years....");
}

__attribute__((noinline))
static void submit(void)
{
    char buf[64];
    char tmp[32];

    puts("1000x1000x1000x1000");
    printf("> ");

    ssize_t nread = read(0, tmp, sizeof(tmp)-1);
    if (nread <= 0)
        exit(1);

    tmp[nread] = 0;

    int n = atoi(tmp);

    if (n < 128)
    {
        unsigned char budget = n;

        printf("Send %u bytes:\n> ", budget);

        read(0, buf, budget);

        puts("done");
    }
    else
    {
        puts("too large");
    }
}

int main(void)
{
    setup();
    banner();

    while (1)
    {
        puts("\n1) submit");
        puts("2) exit");
        printf("> ");

        char c[8];

        if (!fgets(c,sizeof(c),stdin))
            break;

        switch(atoi(c))
        {
            case 1:
                submit();
                break;

            case 2:
                return 0;

            default:
                puts("nope");
        }
    }
}