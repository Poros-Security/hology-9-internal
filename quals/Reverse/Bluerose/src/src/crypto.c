#include "crypto.h"

#include <string.h>

static const uint32_t blake_iv[8] = {
    0x6a09e667U, 0xbb67ae85U, 0x3c6ef372U, 0xa54ff53aU,
    0x510e527fU, 0x9b05688cU, 0x1f83d9abU, 0x5be0cd19U
};

static const uint8_t sigma[10][16] = {
    {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15},
    {14,10,4,8,9,15,13,6,1,12,0,2,11,7,5,3},
    {11,8,12,0,5,2,15,13,10,14,3,6,7,1,9,4},
    {7,9,3,1,13,12,11,14,2,6,5,10,4,0,15,8},
    {9,0,5,7,2,4,10,15,14,1,11,12,6,8,3,13},
    {2,12,6,10,0,11,8,3,4,13,7,5,15,14,1,9},
    {12,5,1,15,14,13,4,10,0,7,6,3,9,2,8,11},
    {13,11,7,14,12,1,3,9,5,0,15,4,8,6,2,10},
    {6,15,14,9,11,3,0,8,12,2,13,7,1,4,10,5},
    {10,2,8,4,7,6,1,5,15,11,9,14,3,12,13,0}
};

static uint32_t load32(const uint8_t *p) {
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}

static void store32(uint8_t *p, uint32_t v) {
    p[0] = (uint8_t)v; p[1] = (uint8_t)(v >> 8);
    p[2] = (uint8_t)(v >> 16); p[3] = (uint8_t)(v >> 24);
}

static uint32_t ror32(uint32_t x, unsigned n) { return (x >> n) | (x << (32U - n)); }

#define B2G(a,b,c,d,x,y) do { \
    (a) = (a) + (b) + (x); (d) = ror32((d) ^ (a), 16); \
    (c) = (c) + (d); (b) = ror32((b) ^ (c), 12); \
    (a) = (a) + (b) + (y); (d) = ror32((d) ^ (a), 8); \
    (c) = (c) + (d); (b) = ror32((b) ^ (c), 7); \
} while (0)

static void blake_compress(uint32_t h[8], const uint8_t block[64], uint64_t count, int final) {
    uint32_t m[16], v[16];
    for (unsigned i = 0; i < 16; i++) m[i] = load32(block + i * 4U);
    for (unsigned i = 0; i < 8; i++) { v[i] = h[i]; v[i + 8] = blake_iv[i]; }
    v[12] ^= (uint32_t)count;
    v[13] ^= (uint32_t)(count >> 32);
    if (final) v[14] = ~v[14];
    for (unsigned r = 0; r < 10; r++) {
        B2G(v[0],v[4],v[8],v[12],m[sigma[r][0]],m[sigma[r][1]]);
        B2G(v[1],v[5],v[9],v[13],m[sigma[r][2]],m[sigma[r][3]]);
        B2G(v[2],v[6],v[10],v[14],m[sigma[r][4]],m[sigma[r][5]]);
        B2G(v[3],v[7],v[11],v[15],m[sigma[r][6]],m[sigma[r][7]]);
        B2G(v[0],v[5],v[10],v[15],m[sigma[r][8]],m[sigma[r][9]]);
        B2G(v[1],v[6],v[11],v[12],m[sigma[r][10]],m[sigma[r][11]]);
        B2G(v[2],v[7],v[8],v[13],m[sigma[r][12]],m[sigma[r][13]]);
        B2G(v[3],v[4],v[9],v[14],m[sigma[r][14]],m[sigma[r][15]]);
    }
    for (unsigned i = 0; i < 8; i++) h[i] ^= v[i] ^ v[i + 8];
}

int rose_blake2s(uint8_t *out, size_t out_len, const uint8_t *key, size_t key_len,
                 const uint8_t *data, size_t data_len) {
    if (out == NULL || out_len == 0 || out_len > 32 || key_len > 32 ||
        (key_len != 0 && key == NULL) || (data_len != 0 && data == NULL)) return 0;
    uint32_t h[8];
    for (unsigned i = 0; i < 8; i++) h[i] = blake_iv[i];
    h[0] ^= 0x01010000U ^ (uint32_t)(key_len << 8) ^ (uint32_t)out_len;
    uint64_t count = 0;
    uint8_t block[64];
    if (key_len != 0) {
        memset(block, 0, sizeof block);
        memcpy(block, key, key_len);
        if (data_len == 0) {
            blake_compress(h, block, 64, 1);
            goto done;
        }
        blake_compress(h, block, 64, 0);
        count = 64;
    }
    while (data_len > 64) {
        memcpy(block, data, 64);
        count += 64;
        blake_compress(h, block, count, 0);
        data += 64;
        data_len -= 64;
    }
    memset(block, 0, sizeof block);
    if (data_len != 0) memcpy(block, data, data_len);
    count += data_len;
    blake_compress(h, block, count, 1);
done:
    for (size_t i = 0; i < out_len; i++) out[i] = (uint8_t)(h[i / 4U] >> (8U * (i % 4U)));
    rose_burn(block, sizeof block);
    rose_burn(h, sizeof h);
    return 1;
}

#undef B2G

void rose_stream_xor(uint8_t *data, size_t length, const uint8_t key[32],
                     const uint8_t nonce[12], uint32_t counter) {
    uint8_t input[16], stream[32];
    memcpy(input, nonce, 12);
    while (length != 0) {
        store32(input + 12, counter++);
        rose_blake2s(stream, sizeof stream, key, 32, input, sizeof input);
        const size_t take = length < sizeof stream ? length : sizeof stream;
        for (size_t i = 0; i < take; i++) data[i] ^= stream[i];
        data += take;
        length -= take;
    }
    rose_burn(input, sizeof input);
    rose_burn(stream, sizeof stream);
}

int rose_constant_time_equal(const uint8_t *a, const uint8_t *b, size_t length) {
    uint8_t difference = 0;
    for (size_t i = 0; i < length; i++) difference |= (uint8_t)(a[i] ^ b[i]);
    return difference == 0;
}

void rose_burn(void *data, size_t length) {
    volatile uint8_t *p = (volatile uint8_t *)data;
    while (length-- != 0) *p++ = 0;
}
