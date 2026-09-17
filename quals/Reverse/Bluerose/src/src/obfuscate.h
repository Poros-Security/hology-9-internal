#ifndef BLUEROSE_OBFUSCATE_H
#define BLUEROSE_OBFUSCATE_H

/* xollvm reads these annotations only in the dedicated obfuscated build. */
#if defined(BLUEROSE_XOLLVM) && defined(__clang__)
#define ROSE_OBF(profile) __attribute__((annotate("obf: " profile)))
#else
#define ROSE_OBF(profile)
#endif

#define ROSE_OBF_ARITH \
    ROSE_OBF("mba(preset=medium), substitution(loop=1), constenc")
#define ROSE_OBF_CONTROL \
    ROSE_OBF("split, bcf(prob=25), flattening(minBlocks=3), constenc")
#define ROSE_OBF_DECODE \
    ROSE_OBF("split, substitution(loop=1), flattening(minBlocks=3)")

#endif
