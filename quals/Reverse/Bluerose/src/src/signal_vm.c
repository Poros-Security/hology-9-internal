#define _GNU_SOURCE
#include "signal_vm.h"

#include "rosevm.h"

#include <signal.h>
#include <stdalign.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <ucontext.h>
#include <unistd.h>

enum FaultFamily { FF_ILL = 1, FF_MEM = 2, FF_CTL = 3, FF_TRAP = 4 };

static RoseVm *volatile active_vm;
static volatile sig_atomic_t active_family;
static volatile sig_atomic_t installed;
static alignas(16) unsigned char signal_stack[64U * 1024U];

static uint64_t rol64(uint64_t x, unsigned n) {
    n &= 63U;
    return n == 0 ? x : (x << n) | (x >> (64U - n));
}

static uint64_t ror64(uint64_t x, unsigned n) {
    n &= 63U;
    return n == 0 ? x : (x >> n) | (x << (64U - n));
}

static uint64_t avalanche(uint64_t x) {
    x ^= x >> 30;
    x *= UINT64_C(0xbf58476d1ce4e5b9);
    x ^= x >> 27;
    x *= UINT64_C(0x94d049bb133111eb);
    return x ^ (x >> 31);
}

static uint64_t folded_meta(const RoseVm *vm) {
    const RosePositionInfo *p = &vm->input.position;
    uint64_t x = p->occupied ^ rol64(p->white_occupied, 7) ^ rol64(p->black_occupied, 37);
    x ^= p->piece_signature;
    x ^= (uint64_t)p->castling << 56;
    x ^= (uint64_t)p->ep_square << 40;
    x ^= (uint64_t)p->halfmove_clock << 16;
    x ^= p->fullmove_number;
    return x;
}

static void bad_signal(int sig) {
    _exit(128 + sig);
}

static void ill_handler(int sig, siginfo_t *info, void *opaque) {
    (void)info;
    if (sig != SIGILL || active_family != FF_ILL || active_vm == NULL) bad_signal(sig);
    RoseVm *vm = active_vm;
    ucontext_t *uc = (ucontext_t *)opaque;
    uint64_t a = (uint64_t)uc->uc_mcontext.gregs[REG_R12];
    const uint64_t b = (uint64_t)uc->uc_mcontext.gregs[REG_R13];
    switch (vm->current.op) {
        case RV_XOR: a ^= b; break;
        case RV_ADD: a += b; break;
        case RV_MUL: a *= b; break;
        case RV_ROL: a = rol64(a, vm->current.imm); break;
        case RV_ROR: a = ror64(a, vm->current.imm); break;
        default: bad_signal(sig);
    }
    uc->uc_mcontext.gregs[REG_R12] = (greg_t)a;
    uc->uc_mcontext.gregs[REG_RIP] += 2;
}

static void mem_handler(int sig, siginfo_t *info, void *opaque) {
    (void)info;
    if (sig != SIGSEGV || active_family != FF_MEM || active_vm == NULL) bad_signal(sig);
    RoseVm *vm = active_vm;
    ucontext_t *uc = (ucontext_t *)opaque;
    uint64_t a = (uint64_t)uc->uc_mcontext.gregs[REG_R12];
    switch (vm->current.op) {
        case RV_LDC:
            if (vm->current.imm >= vm->program.constant_count) bad_signal(sig);
            a = vm->program.constants[vm->current.imm];
            break;
        case RV_LDMOVE: a = vm->input.move; break;
        case RV_LDBOARD: a = vm->input.position.hash; break;
        case RV_LDMETA: a = folded_meta(vm); break;
        case RV_LDINDEX: a = vm->input.ply; break;
        case RV_LDSTATE: a = vm->key.s[vm->current.imm & 3U]; break;
        case RV_STSTATE: vm->key.s[vm->current.imm & 3U] = a; break;
        case RV_LDSIDE: a = vm->input.position.side_to_move; break;
        case RV_LDDEBUG: a = vm->input.debug_word; break;
        default: bad_signal(sig);
    }
    uc->uc_mcontext.gregs[REG_R12] = (greg_t)a;
    uc->uc_mcontext.gregs[REG_RIP] += 3;
}

static void ctl_handler(int sig, siginfo_t *info, void *opaque) {
    (void)info;
    if (sig != SIGFPE || active_family != FF_CTL || active_vm == NULL) bad_signal(sig);
    RoseVm *vm = active_vm;
    ucontext_t *uc = (ucontext_t *)opaque;
    const uint64_t a = (uint64_t)uc->uc_mcontext.gregs[REG_R12];
    int64_t next = (int64_t)uc->uc_mcontext.gregs[REG_R14];
    const int8_t displacement = (int8_t)vm->current.imm;
    switch (vm->current.op) {
        case RV_BRBIT:
            if (((a >> (vm->current.b & 63U)) & 1U) != 0) next += displacement;
            break;
        case RV_JNZ:
            if (a != 0) next += displacement;
            break;
        case RV_JMP: next += displacement; break;
        case RV_HALT: vm->halted = 1; break;
        default: bad_signal(sig);
    }
    uc->uc_mcontext.gregs[REG_R14] = (greg_t)next;
    uc->uc_mcontext.gregs[REG_RIP] += 3;
}

static void trap_handler(int sig, siginfo_t *info, void *opaque) {
    (void)info;
    if (sig != SIGTRAP || active_family != FF_TRAP || active_vm == NULL) bad_signal(sig);
    RoseVm *vm = active_vm;
    ucontext_t *uc = (ucontext_t *)opaque;
    uint64_t a = (uint64_t)uc->uc_mcontext.gregs[REG_R12];
    const uint64_t b = (uint64_t)uc->uc_mcontext.gregs[REG_R13];
    switch (vm->current.op) {
        case RV_MIX:
            a = avalanche(a + rol64(b, vm->current.imm) + UINT64_C(0x517cc1b727220a95));
            uc->uc_mcontext.gregs[REG_R12] = (greg_t)a;
            break;
        case RV_KEYSTEP: {
            const unsigned salt = vm->current.imm;
            const uint64_t x = a ^ rol64(b, salt) ^ vm->input.position.hash ^
                               ((uint64_t)vm->input.ply * UINT64_C(0x9e3779b97f4a7c15));
            const uint64_t s0 = vm->key.s[0], s1 = vm->key.s[1];
            const uint64_t s2 = vm->key.s[2], s3 = vm->key.s[3];
            const uint64_t n0 = s0 + avalanche(x ^ s2);
            const uint64_t n1 = s1 ^ rol64(s0, 17U + salt % 31U);
            const uint64_t n2 = s2 + (s1 ^ vm->input.position.piece_signature);
            const uint64_t n3 = s3 ^ avalanche(s2 + vm->input.position.occupied + x);
            vm->key.s[0] = rol64(n0 ^ n3, 13);
            vm->key.s[1] = rol64(n1 + n0, 29);
            vm->key.s[2] = rol64(n2 ^ n1, 41);
            vm->key.s[3] = rol64(n3 + n2, 7);
            break;
        }
        case RV_OUTPUT:
            for (unsigned lane = 0; lane < 4; lane++)
                for (unsigned byte = 0; byte < 8; byte++)
                    vm->output[lane * 8U + byte] = (uint8_t)(vm->key.s[lane] >> (byte * 8U));
            vm->output_ready = 1;
            break;
        default: bad_signal(sig);
    }
    /* INT3 reports the address after its one-byte instruction. */
}

int rose_signal_install(void) {
    if (installed) return 1;
    stack_t ss;
    memset(&ss, 0, sizeof ss);
    ss.ss_sp = signal_stack;
    ss.ss_size = sizeof signal_stack;
    if (sigaltstack(&ss, NULL) != 0) return 0;

    const int signals[] = {SIGILL, SIGSEGV, SIGFPE, SIGTRAP};
    void (*handlers[])(int, siginfo_t *, void *) = {
        ill_handler, mem_handler, ctl_handler, trap_handler
    };
    for (unsigned i = 0; i < 4; i++) {
        struct sigaction sa;
        memset(&sa, 0, sizeof sa);
        sa.sa_sigaction = handlers[i];
        sa.sa_flags = SA_SIGINFO | SA_ONSTACK;
        sigfillset(&sa.sa_mask);
        if (sigaction(signals[i], &sa, NULL) != 0) return 0;
    }
    installed = 1;
    return 1;
}

static int family_for(uint8_t op) {
    static const uint8_t ill[] = {RV_XOR, RV_ADD, RV_MUL, RV_ROL, RV_ROR};
    static const uint8_t mem[] = {RV_LDC, RV_LDMOVE, RV_LDBOARD, RV_LDMETA, RV_LDINDEX,
                                  RV_LDSTATE, RV_STSTATE, RV_LDSIDE, RV_LDDEBUG};
    static const uint8_t ctl[] = {RV_BRBIT, RV_JNZ, RV_JMP, RV_HALT};
    static const uint8_t trap[] = {RV_MIX, RV_KEYSTEP, RV_OUTPUT};
    const uint8_t *sets[] = {ill, mem, ctl, trap};
    const size_t sizes[] = {sizeof ill, sizeof mem, sizeof ctl, sizeof trap};
    for (int family = 0; family < 4; family++)
        for (size_t i = 0; i < sizes[family]; i++)
            if (sets[family][i] == op) return family + 1;
    return 0;
}

int rose_signal_execute(RoseVm *vm, const RoseInsn *insn, uint8_t *next_pc) {
    const int family = family_for(insn->op);
    if (family == 0 || vm == NULL || next_pc == NULL) return 0;
    register uint64_t r12 __asm__("r12") = vm->regs[insn->a & 3U];
    register uint64_t r13 __asm__("r13") = vm->regs[insn->b & 3U];
    register uint64_t r14 __asm__("r14") = *next_pc;
    register uint64_t r15 __asm__("r15") = vm->key.s[insn->imm & 3U];
    vm->current = *insn;
    active_vm = vm;
    active_family = family;
    __asm__ volatile("" ::: "memory");
    if (family == FF_ILL) {
        __asm__ volatile("ud2" : "+r"(r12), "+r"(r13), "+r"(r14), "+r"(r15) :: "memory", "cc");
    } else if (family == FF_MEM) {
        __asm__ volatile("xor %%eax, %%eax; .byte 0x48,0x8b,0x00"
                         : "+r"(r12), "+r"(r13), "+r"(r14), "+r"(r15)
                         :: "rax", "memory", "cc");
    } else if (family == FF_CTL) {
        __asm__ volatile("mov $1, %%eax; xor %%edx, %%edx; xor %%ecx, %%ecx; .byte 0x48,0xf7,0xf1"
                         : "+r"(r12), "+r"(r13), "+r"(r14), "+r"(r15)
                         :: "rax", "rcx", "rdx", "memory", "cc");
    } else {
        __asm__ volatile("int3" : "+r"(r12), "+r"(r13), "+r"(r14), "+r"(r15) :: "memory", "cc");
    }
    __asm__ volatile("" ::: "memory");
    active_family = 0;
    active_vm = NULL;
    vm->regs[insn->a & 3U] = r12;
    *next_pc = (uint8_t)r14;
    return 1;
}
