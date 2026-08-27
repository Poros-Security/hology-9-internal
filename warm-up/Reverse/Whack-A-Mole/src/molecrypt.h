#ifndef MOLECRYPT_H
#define MOLECRYPT_H

#include <stddef.h>
#include <stdint.h>

#define GRID       10
#define NUM_HOLES  (GRID * GRID)
#define PATH_LEN   12
#define HOLE_SIZE  256

#define MOLE_SEED  0x5EEDCAFEB00B1E5FULL

/* plaintext layout of a hole (only the generator ever writes one) */
#define OFF_MAGIC    0
#define OFF_ROUND    4
#define OFF_FRAGLEN  5
#define OFF_FRAG     6

uint64_t mole_mix64(uint64_t x);
void     mole_keystream(uint64_t state, uint8_t pick, uint8_t *out, size_t n);
void     mole_crypt(const uint8_t *in, uint8_t *out, size_t n,
                    uint64_t state, uint8_t pick);
uint64_t mole_advance(uint64_t s, uint8_t pick, const uint8_t *plain, size_t n);

#endif /* MOLECRYPT_H */
