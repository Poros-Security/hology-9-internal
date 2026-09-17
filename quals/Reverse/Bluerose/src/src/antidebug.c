#include "antidebug.h"

#include <fcntl.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

static int tracer_present(void) {
    char buffer[2048];
    const int fd = open("/proc/self/status", O_RDONLY | O_CLOEXEC);
    if (fd < 0) return 0;
    const ssize_t got = read(fd, buffer, sizeof buffer - 1U);
    close(fd);
    if (got <= 0) return 0;
    buffer[got] = '\0';
    const char *line = strstr(buffer, "TracerPid:");
    if (line == NULL) return 0;
    line += 10;
    while (*line == ' ' || *line == '\t') line++;
    return *line >= '1' && *line <= '9';
}

static int timing_disturbed(void) {
    struct timespec before, after;
    if (clock_gettime(CLOCK_MONOTONIC, &before) != 0) return 0;
    volatile uint64_t x = UINT64_C(0x9e3779b97f4a7c15);
    for (unsigned i = 0; i < 50000; i++) {
        x ^= x >> 12; x ^= x << 25; x ^= x >> 27;
        x *= UINT64_C(0x2545f4914f6cdd1d);
    }
    (void)x;
    if (clock_gettime(CLOCK_MONOTONIC, &after) != 0) return 0;
    const int64_t ns = (int64_t)(after.tv_sec - before.tv_sec) * INT64_C(1000000000) +
                       (after.tv_nsec - before.tv_nsec);
    return ns > INT64_C(250000000);
}

uint64_t rose_debug_word(void) {
    uint64_t word = 0;
    if (tracer_present()) word ^= UINT64_C(0x0200000000000000);
    if (timing_disturbed()) word ^= UINT64_C(0x0000004000000000);
    return word;
}
