CC ?= gcc
CFLAGS ?= -O2 -static -no-pie -fno-stack-protector -Wall -Wextra

all: exploit

exploit: exploit.c
	$(CC) $(CFLAGS) $< -o $@

clean:
	rm -f exploit
