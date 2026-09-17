#ifndef BLUEROSE_SIGNAL_VM_H
#define BLUEROSE_SIGNAL_VM_H

#include <stdint.h>

struct RoseVm;
struct RoseInsn;

int rose_signal_install(void);
int rose_signal_execute(struct RoseVm *vm, const struct RoseInsn *insn, uint8_t *next_pc);

#endif
