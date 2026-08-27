#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define MAX_NOTES 48
#define MAX_SIZE  0x800

#define EMPTY 0
#define LIVE  1
#define FREED 2

typedef struct note {
    void *ptr;
    size_t size;
    unsigned int state;
} note_t;

static note_t notes[MAX_NOTES];

__attribute__((aligned(16))) static char sample_path[0x100] = "/tmp/lakaela-no-ticket";
__attribute__((aligned(16))) static uintptr_t sealed_ticket[4];

static void setup(void) {
    setbuf(stdin, NULL);
    setbuf(stdout, NULL);
    setbuf(stderr, NULL);
}

static void die(const char *msg) {
    puts(msg);
    exit(1);
}

static unsigned long read_ulong(void) {
    char buf[0x40];
    char *end = NULL;

    if (!fgets(buf, sizeof(buf), stdin)) {
        exit(0);
    }
    errno = 0;
    unsigned long v = strtoul(buf, &end, 0);
    if (errno != 0) {
        die("bad number");
    }
    return v;
}

static long read_long(void) {
    char buf[0x40];
    char *end = NULL;

    if (!fgets(buf, sizeof(buf), stdin)) {
        exit(0);
    }
    errno = 0;
    long v = strtol(buf, &end, 0);
    if (errno != 0) {
        die("bad number");
    }
    return v;
}

static void read_exact(unsigned char *dst, size_t n) {
    size_t got = 0;
    while (got < n) {
        ssize_t r = read(STDIN_FILENO, dst + got, n - got);
        if (r <= 0) {
            exit(0);
        }
        got += (size_t)r;
    }
}

static int valid_idx(unsigned long idx) {
    return idx < MAX_NOTES;
}

static void menu(void) {
    puts("");
    puts("[ lakaela forge ]");
    puts("1. mine ore");
    puts("2. temper ore");
    puts("3. inspect ore");
    puts("4. discard ore");
    puts("5. calibrate mold");
    puts("6. crack tag");
    puts("7. quench ore");
    puts("8. submit smithing ticket");
    puts("9. clock out");
    printf("kaela> ");
}

static void create_entry(void) {
    printf("index: ");
    unsigned long idx = read_ulong();
    if (!valid_idx(idx)) {
        puts("invalid index");
        return;
    }
    if (notes[idx].state == LIVE) {
        puts("slot occupied");
        return;
    }

    printf("size: ");
    unsigned long size = read_ulong();
    if (size == 0 || size > MAX_SIZE) {
        puts("invalid size");
        return;
    }

    void *p = malloc(size);
    if (!p) {
        die("malloc failed");
    }
    notes[idx].ptr = p;
    notes[idx].size = size;
    notes[idx].state = LIVE;
    puts("ore indexed");
}

static void edit_entry(void) {
    printf("index: ");
    unsigned long idx = read_ulong();
    if (!valid_idx(idx) || notes[idx].state != LIVE) {
        puts("not live");
        return;
    }

    printf("length: ");
    unsigned long len = read_ulong();
    if (len > notes[idx].size) {
        puts("too long");
        return;
    }

    printf("data: ");
    read_exact((unsigned char *)notes[idx].ptr, len);
    puts("tempered");
}

static void view_entry(void) {
    printf("index: ");
    unsigned long idx = read_ulong();
    if (!valid_idx(idx) || notes[idx].state == EMPTY || notes[idx].ptr == NULL) {
        puts("empty");
        return;
    }

    puts("BEGIN-DATA");
    write(STDOUT_FILENO, notes[idx].ptr, notes[idx].size);
    puts("\nEND-DATA");
}

static void delete_entry(void) {
    printf("index: ");
    unsigned long idx = read_ulong();
    if (!valid_idx(idx) || notes[idx].state != LIVE) {
        puts("not live");
        return;
    }

    free(notes[idx].ptr);
    notes[idx].state = FREED;
    puts("discarded");
}

static void calibrate_entry(void) {
    printf("index: ");
    unsigned long idx = read_ulong();
    if (!valid_idx(idx) || notes[idx].state != LIVE) {
        puts("not live");
        return;
    }

    printf("offset: ");
    long off = read_long();
    printf("length: ");
    unsigned long len = read_ulong();

    if (off < -0x20 || len > 8 || off + (long)len > (long)notes[idx].size) {
        puts("bad calibration");
        return;
    }

    printf("data: ");
    read_exact((unsigned char *)notes[idx].ptr + off, len);
    puts("mold calibrated");
}

static void peel_label(void) {
    printf("index: ");
    unsigned long idx = read_ulong();
    if (!valid_idx(idx) || notes[idx].state != LIVE || notes[idx].size != 0x88) {
        puts("not peelable");
        return;
    }

    free((unsigned char *)notes[idx].ptr - 0x10);
    puts("tag cracked");
}

static void rinse_entry(void) {
    printf("index: ");
    unsigned long idx = read_ulong();
    if (!valid_idx(idx) || notes[idx].state != FREED || notes[idx].ptr == NULL) {
        puts("not stale");
        return;
    }
    printf("offset: ");
    unsigned long off = read_ulong();
    if (off >= notes[idx].size) {
        puts("bad rinse");
        return;
    }

    ((unsigned char *)notes[idx].ptr)[off] = '\0';
    puts("quenched");
}

static void submit_ticket(void) {
    char buf[0x100];
    int fd;

    printf("ticket path: %s\n", sample_path);
    fd = open(sample_path, O_RDONLY);
    if (fd < 0) {
        puts("ticket rejected");
        return;
    }

    ssize_t n = read(fd, buf, sizeof(buf) - 1);
    if (n < 0) {
        close(fd);
        puts("ticket unreadable");
        return;
    }
    buf[n] = '\0';
    close(fd);
    puts("[ ticket contents ]");
    puts(buf);
    puts("[ end ticket ]");
}

static void install_initial_hint(void) {
    sealed_ticket[0] = (uintptr_t)sample_path;
    sealed_ticket[1] = (uintptr_t)notes;
    notes[0].ptr = sealed_ticket;
    notes[0].size = sizeof(sealed_ticket);
    notes[0].state = LIVE;
}

int main(void) {
    setup();
    install_initial_hint();
    puts("lakaela v1.0");
    puts("slot 0 contains a sealed smithing ticket.");

    for (;;) {
        menu();
        unsigned long choice = read_ulong();
        switch (choice) {
        case 1:
            create_entry();
            break;
        case 2:
            edit_entry();
            break;
        case 3:
            view_entry();
            break;
        case 4:
            delete_entry();
            break;
        case 5:
            calibrate_entry();
            break;
        case 6:
            peel_label();
            break;
        case 7:
            rinse_entry();
            break;
        case 8:
            submit_ticket();
            break;
        case 9:
            puts("bye");
            return 0;
        default:
            puts("invalid");
            break;
        }
    }
}
