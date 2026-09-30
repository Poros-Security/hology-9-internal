

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>

#define MAX_BUFS 10
#define MAX_LOGS 4

struct buf_entry {
    char  *data;
    size_t size;
};

static struct buf_entry bufs[MAX_BUFS];
static FILE *logs[MAX_LOGS];
static int   log_active[MAX_LOGS];


static void banner(void) {
    puts("╔═══════════════════════════════════════╗");
    puts("║       FILEKEEPER v2.0                 ║");
    puts("║   Secure File & Buffer Manager        ║");
    puts("╚═══════════════════════════════════════╝");
}

static unsigned long read_ulong(const char *prompt) {
    unsigned long val;
    printf("%s", prompt);
    if (scanf("%lu", &val) != 1) {
        puts("Bad input");
        exit(1);
    }
    getchar(); 
    return val;
}

static void read_str(const char *prompt, char *dst, size_t max) {
    printf("%s", prompt);
    ssize_t n = read(STDIN_FILENO, dst, max);
    if (n > 0 && dst[n - 1] == '\n')
        dst[n - 1] = '\0';
    else if (n > 0)
        dst[n] = '\0';
}

static void menu(void) {
    puts("\n--- Buffer Operations ---");
    puts(" 1. Alloc buffer");
    puts(" 2. Free buffer");
    puts(" 3. Read buffer");
    puts(" 4. Write buffer");
    puts("--- Log Operations ---");
    puts(" 5. Open log");
    puts(" 6. Close log");
    puts(" 7. Write to log");
    puts(" 8. View log info");
    puts("--- System ---");
    puts(" 9. Flush & Exit");
    printf("> ");
}


static void buf_alloc(void) {
    unsigned long idx = read_ulong("Index (0-9): ");
    if (idx >= MAX_BUFS) { puts("Invalid index"); return; }
    if (bufs[idx].data) { puts("Slot occupied"); return; }

    unsigned long size = read_ulong("Size: ");
    if (size == 0 || size > 0x1000) { puts("Bad size (1-4096)"); return; }

    bufs[idx].data = malloc(size);
    if (!bufs[idx].data) { puts("malloc failed"); return; }
    bufs[idx].size = size;
    memset(bufs[idx].data, 0, size);

    printf("[+] Buffer %lu allocated (%lu bytes)\n", idx, size);
}

static void buf_free(void) {
    unsigned long idx = read_ulong("Index (0-9): ");
    if (idx >= MAX_BUFS) { puts("Invalid index"); return; }
    if (!bufs[idx].data) { puts("Empty slot"); return; }

    free(bufs[idx].data);


    printf("[+] Buffer %lu freed\n", idx);
}

static void buf_read(void) {
    unsigned long idx = read_ulong("Index (0-9): ");
    if (idx >= MAX_BUFS) { puts("Invalid index"); return; }
    if (!bufs[idx].data) { puts("Empty slot"); return; }

    puts("Content:");
    write(STDOUT_FILENO, bufs[idx].data, bufs[idx].size);
    putchar('\n');
}

static void buf_write(void) {
    unsigned long idx = read_ulong("Index (0-9): ");
    if (idx >= MAX_BUFS) { puts("Invalid index"); return; }
    if (!bufs[idx].data) { puts("Empty slot"); return; }

    read_str("Data: ", bufs[idx].data, bufs[idx].size);

    printf("[+] Written to buffer %lu\n", idx);
}


static void log_open(void) {
    unsigned long idx = read_ulong("Log slot (0-3): ");
    if (idx >= MAX_LOGS) { puts("Invalid slot"); return; }
    if (log_active[idx]) { puts("Log already open"); return; }


    char path[64];
    snprintf(path, sizeof(path), "/tmp/.fk_log_%lu_%d", idx, getpid());
    logs[idx] = fopen(path, "w+");
    if (!logs[idx]) { puts("fopen failed"); return; }
    log_active[idx] = 1;

    /* Write something so the FILE struct has state */
    fprintf(logs[idx], "=== Log %lu opened ===\n", idx);
    fflush(logs[idx]);

    printf("[+] Log %lu opened (FILE* @ %p)\n", idx, (void *)logs[idx]);
}

static void log_close(void) {
    unsigned long idx = read_ulong("Log slot (0-3): ");
    if (idx >= MAX_LOGS) { puts("Invalid slot"); return; }
    if (!log_active[idx]) { puts("Not open"); return; }

    fclose(logs[idx]);


    log_active[idx] = 0;


    printf("[+] Log %lu closed\n", idx);
}

static void log_write(void) {
    unsigned long idx = read_ulong("Log slot (0-3): ");
    if (idx >= MAX_LOGS) { puts("Invalid slot"); return; }
    if (!log_active[idx]) { puts("Not open"); return; }

    char line[256];
    read_str("Log line: ", line, sizeof(line) - 1);

    fprintf(logs[idx], "%s\n", line);
    printf("[+] Written to log %lu\n", idx);
}

static void log_info(void) {
    puts("\n=== Log Status ===");
    for (int i = 0; i < MAX_LOGS; i++) {
        printf("  [%d] FILE*=%p  active=%d\n",
               i, (void *)logs[i], log_active[i]);
    }
}



static void flush_and_exit(void) {
    puts("[*] Flushing all logs...");

    for (int i = 0; i < MAX_LOGS; i++) {
        if (logs[i]) {
            fflush(logs[i]);
        }
    }

    puts("[*] Goodbye!");

    exit(0);
}

int main(void) {
    setvbuf(stdin,  NULL, _IONBF, 0);
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    banner();


    printf("[*] Gift: puts @ %p\n", (void *)puts);

    while (1) {
        menu();
        unsigned long choice = read_ulong("");

        switch (choice) {
        case 1: buf_alloc();       break;
        case 2: buf_free();        break;
        case 3: buf_read();        break;
        case 4: buf_write();       break;
        case 5: log_open();        break;
        case 6: log_close();       break;
        case 7: log_write();       break;
        case 8: log_info();        break;
        case 9: flush_and_exit();  break;
        default: puts("Invalid choice"); break;
        }
    }
}
