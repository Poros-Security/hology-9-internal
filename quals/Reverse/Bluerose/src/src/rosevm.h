#ifndef BLUEROSE_ROSEVM_H
#define BLUEROSE_ROSEVM_H

#include <stdint.h>

#include "board_wrap.h"
#include "bytecode.h"

enum RoseOpcode {
    RV_LDC = 0x91,
    RV_LDMOVE = 0xd3,
    RV_LDBOARD = 0x48,
    RV_LDMETA = 0xb5,
    RV_LDINDEX = 0x0c,
    RV_LDSTATE = 0xe1,
    RV_STSTATE = 0x63,
    RV_LDSIDE = 0x37,
    RV_LDDEBUG = 0xad,
    RV_XOR = 0x54,
    RV_ADD = 0xc7,
    RV_MUL = 0x82,
    RV_ROL = 0xf0,
    RV_ROR = 0x3b,
    RV_BRBIT = 0xa4,
    RV_JNZ = 0x11,
    RV_JMP = 0xde,
    RV_HALT = 0x40,
    RV_MIX = 0x75,
    RV_KEYSTEP = 0xca,
    RV_OUTPUT = 0x24
};

typedef struct {
    uint64_t s[4];
} RoseKeyState;

typedef struct {
    RoseMove move;
    RosePositionInfo position;
    uint64_t debug_word;
    uint16_t ply;
    uint8_t stage;
} RoseVmInput;

typedef struct RoseVm {
    RoseKeyState key;
    uint64_t regs[4];
    RoseVmInput input;
    RoseProgram program;
    RoseInsn current;
    uint8_t output[32];
    uint8_t halted;
    uint8_t output_ready;
} RoseVm;

int rosevm_global_init(void);
int rosevm_reset(RoseVm *vm, uint64_t debug_word);
int rosevm_step(RoseVm *vm, RoseMove move, const RosePositionInfo *position, uint16_t ply);
int rosevm_finish(RoseVm *vm, const RosePositionInfo *position, uint16_t ply, uint8_t key[32]);

#endif
