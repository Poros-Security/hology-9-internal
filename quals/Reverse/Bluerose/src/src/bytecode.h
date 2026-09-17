#ifndef BLUEROSE_BYTECODE_H
#define BLUEROSE_BYTECODE_H

#include <stddef.h>
#include <stdint.h>

typedef struct RoseInsn {
    uint8_t op;
    uint8_t a;
    uint8_t b;
    uint8_t imm;
} RoseInsn;

typedef struct {
    uint64_t constants[16];
    RoseInsn insns[96];
    uint8_t constant_count;
    uint8_t instruction_count;
    uint8_t entry[3];
} RoseProgram;

int rose_bytecode_decode(RoseProgram *program);
const uint8_t *rose_bytecode_blob(size_t *length);

#endif
