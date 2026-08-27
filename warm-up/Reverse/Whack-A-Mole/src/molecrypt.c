#include <string.h>

#include "molecrypt.h"

/*
 * The salt is stored masked so that the literal never lands in .rodata as a
 * printable run -- one of the ship invariants is that `strings mallet` gives
 * away neither the flag nor the magic. `volatile` keeps the optimiser from
 * folding the eight loads back into one 64-bit constant.
 *
 * This is layout hygiene, not anti-debugging: a disassembler shows the mask
 * and the bytes side by side.
 */
#define SALT_MASK 0x5A
static volatile uint8_t SALT_ENC[8] = {
    'M' ^ SALT_MASK, '0' ^ SALT_MASK, 'L' ^ SALT_MASK, 'E' ^ SALT_MASK,
    'H' ^ SALT_MASK, '1' ^ SALT_MASK, 'L' ^ SALT_MASK, 'L' ^ SALT_MASK,
};

uint64_t mole_mix64(uint64_t x)
{
    x ^= x >> 30;
    x *= 0xBF58476D1CE4E5B9ULL;
    x ^= x >> 27;
    x *= 0x94D049BB133111EBULL;
    x ^= x >> 31;
    return x;
}

void mole_keystream(uint64_t state, uint8_t pick, uint8_t *out, size_t n)
{
    uint64_t x = state ^ (0x9E3779B97F4A7C15ULL * ((uint64_t)pick + 1));
    size_t i;
    int j;

    for (j = 0; j < 8; j++)
        x ^= (uint64_t)(uint8_t)(SALT_ENC[j] ^ SALT_MASK) << (j * 8);

    for (i = 0; i < n; i += 8) {
        uint8_t blk[8];
        size_t take = (n - i < 8) ? (n - i) : 8;

        x = mole_mix64(x);
        for (j = 0; j < 8; j++)
            blk[j] = (uint8_t)(x >> (j * 8));
        memcpy(out + i, blk, take);
    }
}

void mole_crypt(const uint8_t *in, uint8_t *out, size_t n,
                uint64_t state, uint8_t pick)
{
    uint8_t ks[HOLE_SIZE];
    size_t i;

    while (n > 0) {
        size_t chunk = (n < HOLE_SIZE) ? n : HOLE_SIZE;

        mole_keystream(state, pick, ks, chunk);
        for (i = 0; i < chunk; i++)
            out[i] = in[i] ^ ks[i];
        in += chunk;
        out += chunk;
        n -= chunk;
    }
}

uint64_t mole_advance(uint64_t s, uint8_t pick, const uint8_t *plain, size_t n)
{
    uint64_t h = s ^ 0xCBF29CE484222325ULL;
    size_t i;

    h ^= pick;
    h *= 0x100000001B3ULL;
    for (i = 0; i < n; i++) {
        h ^= plain[i];
        h *= 0x100000001B3ULL;
    }
    return h;
}
