#ifndef SUIWALLET_CA_H
#define SUIWALLET_CA_H

#include <stddef.h>
#include <stdint.h>

#if defined(__has_include)
#if __has_include(<tee_client_api.h>)
#include <tee_client_api.h>
#else
#include <opentee/tee_client_api.h>
#endif
#else
#include <tee_client_api.h>
#endif

#define SUIWALLET_TA_UUID \
	{ 0x4b5fdab2, 0xd3cd, 0x4aa4, { 0xa3, 0x87, 0x72, 0x90, 0x21, 0x34, 0x89, 0x50 } }

#define SUIWALLET_CMD_CREATE_WALLET   0
#define SUIWALLET_CMD_DELETE_WALLET   1
#define SUIWALLET_CMD_RENAME_WALLET   2
#define SUIWALLET_CMD_SHOW_WALLET     3
#define SUIWALLET_CMD_LIST_WALLETS    4
#define SUIWALLET_CMD_PREPARE_BATCH   5
#define SUIWALLET_CMD_SETTLE_BATCH    6
#define SUIWALLET_CMD_SHOW_BATCH      7
#define SUIWALLET_CMD_SESSION_INFO    8

#define SUIWALLET_MAX_WALLETS 8
#define SUIWALLET_VAULT_NAME_SIZE 16
#define SUIWALLET_NOTE_SIZE       32
#define SUIWALLET_COUNTERPARTY_SIZE 16
#define SUIWALLET_MEMO_SIZE   40
#define SUIWALLET_ARENA_SLOTS 64

struct suiwallet_create_req {
	char vault_name[SUIWALLET_VAULT_NAME_SIZE];
	uint64_t opening_balance;
	char last_note[SUIWALLET_NOTE_SIZE];
	uint32_t wallet_id;
};

struct suiwallet_wallet_ref {
	uint32_t wallet_id;
	uint32_t owner_id;
};

struct suiwallet_batch_req {
	uintptr_t entries; /* Reserved; staged entries are supplied via param[2]. */
	uint32_t entry_count;
	uint32_t source_wallet_id;
	uint32_t reserved;
	char memo[SUIWALLET_MEMO_SIZE];
};

/* One staged transfer in a settlement export batch. */
struct suiwallet_ledger_entry {
	uint64_t owner_cookie;
	uint64_t amount;
	uint32_t slot_id;
	uint32_t owner_id;
	char counterparty[SUIWALLET_COUNTERPARTY_SIZE];
	char memo[SUIWALLET_NOTE_SIZE];
};

struct suiwallet_session_info {
	uint32_t owner_id;
	uint32_t live_wallets;
	uint32_t exported_batches;
	uint32_t reserved;
};

/*
 * Parameter conventions used by the reference CA:
 * CREATE:        VALUE_OUTPUT, MEMREF_INPUT, NONE, NONE
 * DELETE:        VALUE_INPUT(slot, owner), NONE, NONE, NONE
 * RENAME:        VALUE_INPUT(slot, owner), MEMREF_INPUT(name), NONE, NONE
 * SHOW:          VALUE_INPUT(slot, owner), MEMREF_OUTPUT, NONE, NONE
 * LIST:          MEMREF_OUTPUT, NONE, NONE, NONE
 * PREPARE_BATCH: VALUE_OUTPUT, MEMREF_INPUT(batch_req), MEMREF_INPUT(entries), NONE
 * SETTLE_BATCH:  VALUE_INPUT(slot, owner), MEMREF_INPUT, VALUE_INOUT, NONE
 * SHOW_BATCH:    VALUE_INPUT(slot, owner), VALUE_INOUT, MEMREF_OUTPUT, NONE
 * SESSION_INFO:  MEMREF_OUTPUT, NONE, NONE, NONE
 *
 * PREPARE_BATCH copies staged ledger entries from caller-controlled shared
 * memory into an internal settlement cache. The reference CA uses a dedicated
 * shared arena for those entries so players can iterate quickly on custom
 * layouts.
 */

#endif
