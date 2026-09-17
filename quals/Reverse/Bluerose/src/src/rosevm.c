#include "rosevm.h"

#include "signal_vm.h"

#include <string.h>

static int run_entry(RoseVm *vm, unsigned stage) {
    if (stage >= 3) return 0;
    uint8_t pc = vm->program.entry[stage];
    vm->halted = 0;
    memset(vm->regs, 0, sizeof vm->regs);
    for (unsigned steps = 0; steps < 256 && !vm->halted; steps++) {
        if (pc >= vm->program.instruction_count) return 0;
        uint8_t next = (uint8_t)(pc + 1U);
        if (!rose_signal_execute(vm, &vm->program.insns[pc], &next)) return 0;
        pc = next;
    }
    return vm->halted != 0;
}

int rosevm_global_init(void) {
    return rose_signal_install();
}

int rosevm_reset(RoseVm *vm, uint64_t debug_word) {
    memset(vm, 0, sizeof *vm);
    if (!rose_bytecode_decode(&vm->program)) return 0;
    vm->input.debug_word = debug_word;
    vm->input.stage = 0;
    return run_entry(vm, 0);
}

int rosevm_step(RoseVm *vm, RoseMove move_value, const RosePositionInfo *position, uint16_t ply) {
    vm->input.move = move_value;
    vm->input.position = *position;
    vm->input.ply = ply;
    vm->input.stage = 1;
    vm->output_ready = 0;
    return run_entry(vm, 1);
}

int rosevm_finish(RoseVm *vm, const RosePositionInfo *position, uint16_t ply, uint8_t key[32]) {
    vm->input.move = 0;
    vm->input.position = *position;
    vm->input.ply = ply;
    vm->input.stage = 2;
    vm->output_ready = 0;
    if (!run_entry(vm, 2) || !vm->output_ready) return 0;
    memcpy(key, vm->output, 32);
    return 1;
}
