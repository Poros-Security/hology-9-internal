#include "zobrist.h"
#include "obfuscate.h"

/* Fixed, build-time domains. No runtime randomness is used. */
ROSE_OBF_ARITH uint64_t rose_zobrist_word(uint64_t domain, uint64_t index) {
    uint64_t z = UINT64_C(0x6a09e667f3bcc909);
    z ^= domain * UINT64_C(0x9e3779b97f4a7c15);
    z ^= (index + UINT64_C(0x100000001b3)) * UINT64_C(0xbf58476d1ce4e5b9);
    z ^= z >> 30;
    z *= UINT64_C(0xbf58476d1ce4e5b9);
    z ^= z >> 27;
    z *= UINT64_C(0x94d049bb133111eb);
    z ^= z >> 31;
    return z;
}
