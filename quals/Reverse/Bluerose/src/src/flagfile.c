#include "flagfile.h"

#include "crypto.h"
#include "obfuscate.h"

#include <stdio.h>
#include <string.h>

#define BRSE_HEADER 24U
#define BRSE_TAG 32U
#define BRSE_LIMIT 4096U

static uint16_t load16(const uint8_t *p) { return (uint16_t)p[0] | (uint16_t)p[1] << 8; }
static uint32_t load32le(const uint8_t *p) {
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}

ROSE_OBF_ARITH int rose_flag_open(const char *path, const uint8_t master[32],
                                  char *plaintext, size_t capacity) {
    uint8_t file[BRSE_HEADER + BRSE_LIMIT + BRSE_TAG];
    FILE *handle = fopen(path, "rb");
    if (handle == NULL) return 0;
    const size_t length = fread(file, 1, sizeof file, handle);
    const int extra = fgetc(handle);
    fclose(handle);
    if (length < BRSE_HEADER + BRSE_TAG || extra != EOF || memcmp(file, "BRSE", 4) != 0 ||
        load16(file + 4) != 1 || load16(file + 6) != 0) return 0;
    const uint32_t cipher_len = load32le(file + 8);
    if (cipher_len == 0 || cipher_len > BRSE_LIMIT ||
        length != BRSE_HEADER + (size_t)cipher_len + BRSE_TAG || capacity <= cipher_len) return 0;

    static const uint8_t enc_domain[] = "BRSE-ENC-v1";
    static const uint8_t mac_domain[] = "BRSE-MAC-v1";
    uint8_t enc_key[32], mac_key[32], tag[32];
    if (!rose_blake2s(enc_key, sizeof enc_key, master, 32, enc_domain, sizeof enc_domain - 1) ||
        !rose_blake2s(mac_key, sizeof mac_key, master, 32, mac_domain, sizeof mac_domain - 1) ||
        !rose_blake2s(tag, sizeof tag, mac_key, sizeof mac_key, file, BRSE_HEADER + cipher_len)) return 0;
    const int valid = rose_constant_time_equal(tag, file + BRSE_HEADER + cipher_len, BRSE_TAG);
    if (valid) {
        memcpy(plaintext, file + BRSE_HEADER, cipher_len);
        rose_stream_xor((uint8_t *)plaintext, cipher_len, enc_key, file + 12, 1);
        plaintext[cipher_len] = '\0';
    }
    rose_burn(enc_key, sizeof enc_key); rose_burn(mac_key, sizeof mac_key); rose_burn(tag, sizeof tag);
    if (!valid) plaintext[0] = '\0';
    return valid;
}
