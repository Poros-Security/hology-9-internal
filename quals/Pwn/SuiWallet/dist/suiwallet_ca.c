#include <err.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "suiwallet_ca.h"

static TEEC_Context ctx;
static TEEC_Session session;
static TEEC_SharedMemory arena;
static TEEC_SharedMemory req_shm;
static TEEC_SharedMemory name_shm;
static TEEC_SharedMemory out_shm;
static struct suiwallet_ledger_entry *table;

static void invoke(uint32_t command, TEEC_Operation *op)
{
	uint32_t origin;
	TEEC_Result res = TEEC_InvokeCommand(&session, command, op, &origin);

	if (res != TEEC_SUCCESS)
		errx(1, "TEEC_InvokeCommand(%u): 0x%x origin 0x%x", command, res, origin);
}

static void allocate_shm(TEEC_SharedMemory *shm, size_t size, uint32_t flags, const char *label)
{
	TEEC_Result res;

	shm->size = size;
	shm->flags = flags;
	res = TEEC_AllocateSharedMemory(&ctx, shm);
	if (res != TEEC_SUCCESS)
		errx(1, "TEEC_AllocateSharedMemory(%s): 0x%x", label, res);
	memset(shm->buffer, 0, shm->size);
}

static void release_shm(TEEC_SharedMemory *shm)
{
	TEEC_ReleaseSharedMemory(shm);
}

static uint64_t parse_u64(const char *value)
{
	char *end = NULL;
	uint64_t result = strtoull(value, &end, 0);

	if (!value[0] || (end && *end))
		errx(1, "invalid integer: %s", value);
	return result;
}

static void session_info(void)
{
	struct suiwallet_session_info *info = out_shm.buffer;
	TEEC_Operation op = { 0 };

	memset(info, 0, sizeof(*info));
	op.paramTypes = TEEC_PARAM_TYPES(TEEC_MEMREF_WHOLE, TEEC_NONE, TEEC_NONE, TEEC_NONE);
	op.params[0].memref.parent = &out_shm;
	invoke(SUIWALLET_CMD_SESSION_INFO, &op);
	printf("owner=%#x live=%u exports=%u\n", info->owner_id, info->live_wallets,
		info->exported_batches);
}

static void create_wallet(const char *vault_name, uint64_t opening_balance, const char *last_note)
{
	struct suiwallet_create_req *req = req_shm.buffer;
	TEEC_Operation op = { 0 };

	memset(req, 0, sizeof(*req));
	strncpy(req->vault_name, vault_name, sizeof(req->vault_name) - 1);
	req->opening_balance = opening_balance;
	strncpy(req->last_note, last_note, sizeof(req->last_note) - 1);
	op.paramTypes = TEEC_PARAM_TYPES(TEEC_VALUE_OUTPUT, TEEC_MEMREF_WHOLE, TEEC_NONE, TEEC_NONE);
	op.params[1].memref.parent = &req_shm;
	invoke(SUIWALLET_CMD_CREATE_WALLET, &op);
	printf("wallet=%u\n", op.params[0].value.a);
}

static void delete_wallet(uint32_t slot_id, uint32_t owner_id)
{
	TEEC_Operation op = { 0 };

	op.paramTypes = TEEC_PARAM_TYPES(TEEC_VALUE_INPUT, TEEC_NONE, TEEC_NONE, TEEC_NONE);
	op.params[0].value.a = slot_id;
	op.params[0].value.b = owner_id;
	invoke(SUIWALLET_CMD_DELETE_WALLET, &op);
	puts("ok");
}

static void rename_wallet(uint32_t slot_id, uint32_t owner_id, const char *vault_name)
{
	TEEC_Operation op = { 0 };

	memset(name_shm.buffer, 0, name_shm.size);
	strncpy(name_shm.buffer, vault_name, name_shm.size - 1);
	op.paramTypes = TEEC_PARAM_TYPES(TEEC_VALUE_INPUT, TEEC_MEMREF_WHOLE, TEEC_NONE, TEEC_NONE);
	op.params[0].value.a = slot_id;
	op.params[0].value.b = owner_id;
	op.params[1].memref.parent = &name_shm;
	invoke(SUIWALLET_CMD_RENAME_WALLET, &op);
	puts("ok");
}

static void show_wallet(uint32_t slot_id, uint32_t owner_id)
{
	char *out = out_shm.buffer;
	TEEC_Operation op = { 0 };

	memset(out, 0, out_shm.size);
	op.paramTypes = TEEC_PARAM_TYPES(TEEC_VALUE_INPUT, TEEC_MEMREF_WHOLE, TEEC_NONE, TEEC_NONE);
	op.params[0].value.a = slot_id;
	op.params[0].value.b = owner_id;
	op.params[1].memref.parent = &out_shm;
	invoke(SUIWALLET_CMD_SHOW_WALLET, &op);
	puts(out);
}

static void list_wallets(void)
{
	char *out = out_shm.buffer;
	TEEC_Operation op = { 0 };

	memset(out, 0, out_shm.size);
	op.paramTypes = TEEC_PARAM_TYPES(TEEC_MEMREF_WHOLE, TEEC_NONE, TEEC_NONE, TEEC_NONE);
	op.params[0].memref.parent = &out_shm;
	invoke(SUIWALLET_CMD_LIST_WALLETS, &op);
	fputs(out, stdout);
}

static void stage_entry(size_t index, uint32_t slot_id, uint32_t owner_id, uint64_t amount,
			const char *counterparty, const char *memo)
{
	struct suiwallet_ledger_entry *entry;

	if (index >= SUIWALLET_ARENA_SLOTS)
		errx(1, "arena index out of range");
	entry = &table[index];
	memset(entry, 0, sizeof(*entry));
	entry->owner_cookie = ((uint64_t)owner_id << 32) | slot_id;
	entry->amount = amount;
	entry->slot_id = slot_id;
	entry->owner_id = owner_id;
	strncpy(entry->counterparty, counterparty, sizeof(entry->counterparty) - 1);
	strncpy(entry->memo, memo, sizeof(entry->memo) - 1);
	printf("staged=%zu\n", index);
}

static void prepare_batch(size_t base_index, uint32_t count, uint32_t source_wallet_id, const char *memo)
{
	struct suiwallet_batch_req *req = req_shm.buffer;
	TEEC_Operation op = { 0 };

	if (base_index >= SUIWALLET_ARENA_SLOTS)
		errx(1, "base index out of range");
	memset(req, 0, sizeof(*req));
	req->entry_count = count;
	req->source_wallet_id = source_wallet_id;
	strncpy(req->memo, memo, sizeof(req->memo) - 1);
	op.paramTypes = TEEC_PARAM_TYPES(TEEC_VALUE_OUTPUT, TEEC_MEMREF_WHOLE,
					 TEEC_MEMREF_PARTIAL_INPUT, TEEC_NONE);
	op.params[1].memref.parent = &req_shm;
	op.params[2].memref.parent = &arena;
	op.params[2].memref.offset = base_index * sizeof(*table);
	op.params[2].memref.size = (size_t)count * sizeof(*table);
	invoke(SUIWALLET_CMD_PREPARE_BATCH, &op);
	printf("batch=%u\n", op.params[0].value.a);
}

static void show_batch(uint32_t slot_id, uint32_t owner_id, uint32_t index)
{
	struct suiwallet_ledger_entry *entry = out_shm.buffer;
	TEEC_Operation op = { 0 };
	const unsigned char *raw;
	size_t i;

	memset(entry, 0, sizeof(*entry));
	op.paramTypes = TEEC_PARAM_TYPES(TEEC_VALUE_INPUT, TEEC_VALUE_INOUT, TEEC_MEMREF_WHOLE,
					 TEEC_NONE);
	op.params[0].value.a = slot_id;
	op.params[0].value.b = owner_id;
	op.params[1].value.a = index;
	op.params[2].memref.parent = &out_shm;
	invoke(SUIWALLET_CMD_SHOW_BATCH, &op);
	raw = (const unsigned char *)entry;
	printf("entry owner_cookie=%#" PRIx64 " amount=%#" PRIx64 " slot=%u owner=%#x counterparty=%s memo=%s\n",
		entry->owner_cookie, entry->amount, entry->slot_id, entry->owner_id,
		entry->counterparty, entry->memo);
	printf("raw=");
	for (i = 0; i < sizeof(*entry); ++i)
		printf("%02x", raw[i]);
	putchar('\n');
}

static void settle_batch(uint32_t slot_id, uint32_t owner_id, uint64_t dst, size_t src_index)
{
	TEEC_Operation op = { 0 };

	if (src_index >= SUIWALLET_ARENA_SLOTS)
		errx(1, "arena index out of range");
	op.paramTypes = TEEC_PARAM_TYPES(TEEC_VALUE_INPUT, TEEC_MEMREF_PARTIAL_INPUT, TEEC_VALUE_INOUT,
					 TEEC_NONE);
	op.params[0].value.a = slot_id;
	op.params[0].value.b = owner_id;
	op.params[1].memref.parent = &arena;
	op.params[1].memref.offset = src_index * sizeof(*table);
	op.params[1].memref.size = sizeof(*table);
	op.params[2].value.a = (uint32_t)dst;
	op.params[2].value.b = (uint32_t)(dst >> 32);
	invoke(SUIWALLET_CMD_SETTLE_BATCH, &op);
	puts("ok");
}

static void read_flag(void)
{
	const char *path = getenv("SUIWALLET_FLAG_PATH");
	FILE *fp;
	char line[256];

	if (!path)
		errx(1, "SUIWALLET_FLAG_PATH is not set");
	fp = fopen(path, "r");
	if (!fp)
		err(1, "fopen(%s)", path);
	while (fgets(line, sizeof(line), fp))
		fputs(line, stdout);
	fclose(fp);
}

static void usage(const char *argv0)
{
	fprintf(stderr,
		"usage:\n"
		"  %s session\n"
		"  %s create VAULT OPENING_BALANCE NOTE\n"
		"  %s delete SLOT OWNER\n"
		"  %s rename SLOT OWNER VAULT\n"
		"  %s show SLOT OWNER\n"
		"  %s list\n"
		"  %s stage-entry INDEX SLOT OWNER AMOUNT COUNTERPARTY MEMO\n"
		"  %s prepare-batch BASE COUNT SOURCE_WALLET MEMO\n"
		"  %s show-batch SLOT OWNER INDEX\n"
		"  %s settle-batch SLOT OWNER DST SRC_INDEX\n"
		"  %s flag\n",
		argv0, argv0, argv0, argv0, argv0, argv0, argv0, argv0, argv0, argv0, argv0);
}

int main(int argc, char **argv)
{
	TEEC_UUID uuid = SUIWALLET_TA_UUID;
	uint32_t origin;
	TEEC_Result res;

	res = TEEC_InitializeContext(NULL, &ctx);
	if (res != TEEC_SUCCESS)
		errx(1, "TEEC_InitializeContext: 0x%x", res);
	res = TEEC_OpenSession(&ctx, &session, &uuid, TEEC_LOGIN_PUBLIC, NULL, NULL, &origin);
	if (res != TEEC_SUCCESS)
		errx(1, "TEEC_OpenSession: 0x%x origin 0x%x", res, origin);

	allocate_shm(&arena, SUIWALLET_ARENA_SLOTS * sizeof(*table),
		TEEC_MEM_INPUT | TEEC_MEM_OUTPUT, "arena");
	table = arena.buffer;
	allocate_shm(&req_shm, sizeof(struct suiwallet_batch_req), TEEC_MEM_INPUT, "req");
	allocate_shm(&name_shm, SUIWALLET_VAULT_NAME_SIZE, TEEC_MEM_INPUT, "name");
	allocate_shm(&out_shm, 1024, TEEC_MEM_OUTPUT, "out");

	if (argc < 2) {
		usage(argv[0]);
		return 1;
	}
	if (!strcmp(argv[1], "session")) {
		session_info();
	} else if (!strcmp(argv[1], "create") && argc >= 5) {
		create_wallet(argv[2], parse_u64(argv[3]), argv[4]);
	} else if (!strcmp(argv[1], "delete") && argc >= 4) {
		delete_wallet((uint32_t)parse_u64(argv[2]), (uint32_t)parse_u64(argv[3]));
	} else if (!strcmp(argv[1], "rename") && argc >= 5) {
		rename_wallet((uint32_t)parse_u64(argv[2]), (uint32_t)parse_u64(argv[3]), argv[4]);
	} else if (!strcmp(argv[1], "show") && argc >= 4) {
		show_wallet((uint32_t)parse_u64(argv[2]), (uint32_t)parse_u64(argv[3]));
	} else if (!strcmp(argv[1], "list")) {
		list_wallets();
	} else if (!strcmp(argv[1], "stage-entry") && argc >= 8) {
		stage_entry((size_t)parse_u64(argv[2]), (uint32_t)parse_u64(argv[3]),
			(uint32_t)parse_u64(argv[4]), parse_u64(argv[5]), argv[6], argv[7]);
	} else if (!strcmp(argv[1], "prepare-batch") && argc >= 6) {
		prepare_batch((size_t)parse_u64(argv[2]), (uint32_t)parse_u64(argv[3]),
			(uint32_t)parse_u64(argv[4]), argv[5]);
	} else if (!strcmp(argv[1], "show-batch") && argc >= 5) {
		show_batch((uint32_t)parse_u64(argv[2]), (uint32_t)parse_u64(argv[3]),
			(uint32_t)parse_u64(argv[4]));
	} else if (!strcmp(argv[1], "settle-batch") && argc >= 6) {
		settle_batch((uint32_t)parse_u64(argv[2]), (uint32_t)parse_u64(argv[3]),
			parse_u64(argv[4]), (size_t)parse_u64(argv[5]));
	} else if (!strcmp(argv[1], "flag")) {
		read_flag();
	} else {
		usage(argv[0]);
		return 1;
	}

	release_shm(&out_shm);
	release_shm(&name_shm);
	release_shm(&req_shm);
	release_shm(&arena);
	TEEC_CloseSession(&session);
	TEEC_FinalizeContext(&ctx);
	return 0;
}
