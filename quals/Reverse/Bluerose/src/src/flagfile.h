#ifndef BLUEROSE_FLAGFILE_H
#define BLUEROSE_FLAGFILE_H

#include <stddef.h>
#include <stdint.h>

int rose_flag_open(const char *path, const uint8_t master[32], char *plaintext, size_t capacity);

#endif
