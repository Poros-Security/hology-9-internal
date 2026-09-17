#ifndef BLUEROSE_CRYPTO_H
#define BLUEROSE_CRYPTO_H

#include <stddef.h>
#include <stdint.h>

int rose_blake2s(uint8_t *out, size_t out_len, const uint8_t *key, size_t key_len,
                 const uint8_t *data, size_t data_len);
void rose_stream_xor(uint8_t *data, size_t length, const uint8_t key[32],
                     const uint8_t nonce[12], uint32_t counter);
int rose_constant_time_equal(const uint8_t *a, const uint8_t *b, size_t length);
void rose_burn(void *data, size_t length);

#endif
