#define _GNU_SOURCE

#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char **argv) {
    const char *appdir = getenv("APPDIR");
    char inferred[PATH_MAX];
    char loader[PATH_MAX];
    char library_path[PATH_MAX];
    char executable[PATH_MAX];
    char data_dir[PATH_MAX];
    char *child_argv[260];

    if (appdir == NULL || *appdir == '\0') {
        const ssize_t length = readlink("/proc/self/exe", inferred, sizeof inferred - 1U);
        if (length <= 0 || (size_t)length >= sizeof inferred) {
            fputs("Bluerose: unable to locate AppDir\n", stderr);
            return 127;
        }
        inferred[length] = '\0';
        char *slash = strrchr(inferred, '/');
        if (slash == NULL) return 127;
        *slash = '\0';
        appdir = inferred;
    }

    if (argc > 253 ||
        snprintf(loader, sizeof loader, "%s/usr/lib/ld-linux-x86-64.so.2", appdir) >= (int)sizeof loader ||
        snprintf(library_path, sizeof library_path, "%s/usr/lib", appdir) >= (int)sizeof library_path ||
        snprintf(executable, sizeof executable, "%s/usr/bin/bluerose", appdir) >= (int)sizeof executable ||
        snprintf(data_dir, sizeof data_dir, "%s/usr/share/bluerose", appdir) >= (int)sizeof data_dir) {
        fputs("Bluerose: AppDir path is too long\n", stderr);
        return 127;
    }

    /* An external flag.enc in the launch directory overrides the bundled file. */
    if (access("flag.enc", R_OK) != 0 && chdir(data_dir) != 0) {
        fprintf(stderr, "Bluerose: cannot enter data directory: %s\n", strerror(errno));
        return 127;
    }

    child_argv[0] = loader;
    child_argv[1] = "--inhibit-cache";
    child_argv[2] = "--library-path";
    child_argv[3] = library_path;
    child_argv[4] = executable;
    for (int i = 1; i < argc; i++) child_argv[i + 4] = argv[i];
    child_argv[argc + 4] = NULL;

    execv(loader, child_argv);
    fprintf(stderr, "Bluerose: launcher failed: %s\n", strerror(errno));
    return 127;
}
