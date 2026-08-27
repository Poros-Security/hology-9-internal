/*
 * Parity harness: mirrors molecrypt.py's _parity_dump() exactly.
 * `make check-parity` diffs the two outputs.
 */
#include <stdio.h>

#include "molecrypt.h"

static void put_hex(const uint8_t *b, size_t n)
{
    size_t i;
    for (i = 0; i < n; i++)
        printf("%02x", b[i]);
}

static void emit(uint64_t state, uint8_t pick)
{
    uint8_t ks[HOLE_SIZE];

    mole_keystream(state, pick, ks, HOLE_SIZE);
    printf("state=%016llx pick=%3d mix=%016llx adv=%016llx\n",
           (unsigned long long)state, pick,
           (unsigned long long)mole_mix64(state),
           (unsigned long long)mole_advance(state, pick, ks, HOLE_SIZE));
    printf("  ks=");
    put_hex(ks, HOLE_SIZE);
    printf("\n");
}

int main(void)
{
    static const uint8_t picks[] = { 0, 1, 7, 42, 99, 255 };
    static const size_t shorts[] = { 1, 7, 8, 9, 15, 16, 255, 256 };
    uint8_t ks[HOLE_SIZE];
    uint64_t st = MOLE_SEED;
    size_t i;

    for (i = 0; i < sizeof(picks); i++) {
        emit(st, picks[i]);
        mole_keystream(st, picks[i], ks, HOLE_SIZE);
        st = mole_advance(st, picks[i], ks, HOLE_SIZE);
    }
    for (i = 0; i < 8; i++)
        emit(0xFFFFFFFFFFFFFFFFULL >> (i * 7), (uint8_t)((i * 13) % 100));
    emit(0, 0);
    emit(0xFFFFFFFFFFFFFFFFULL, 99);

    for (i = 0; i < sizeof(shorts) / sizeof(shorts[0]); i++) {
        size_t n = shorts[i];
        mole_keystream(MOLE_SEED, (uint8_t)(n % 100), ks, n);
        printf("short n=%3zu ks=", n);
        put_hex(ks, n);
        printf("\n");
    }
    return 0;
}
