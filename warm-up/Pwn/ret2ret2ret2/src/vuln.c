#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(void);

__attribute__((naked, used))
void pop_rdi_ret(void) {
    __asm__("pop %rdi; ret;");
}

__attribute__((naked, used))
void ret_ret_ret(void) {
    __asm__("ret; ret; ret;");
}

void setup(void) {
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
}

void banner(void) {
    puts("================================");
    puts("          ret2ret2ret2");
    puts("================================");
}

void vuln(void) {
    char buf[64];
    char fmt[96];

    puts("I brought you three returns.");
    puts("Can you bring me a shell?");

    printf("format> ");
    if (!fgets(fmt, sizeof(fmt), stdin)) {
        exit(1);
    }

    printf("echo> ");
    printf(fmt, puts, main, vuln, pop_rdi_ret, ret_ret_ret);
    puts("");

    printf("overflow> ");
    read(0, buf, 256);

    puts("bye");
}

int main(void) {
    setup();
    banner();
    vuln();
    return 0;
}
