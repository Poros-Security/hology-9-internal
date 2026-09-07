CC := gcc
CFLAGS := -Wall -Wextra -Wpedantic -O0 -g -fPIE -fno-stack-protector -D_FORTIFY_SOURCE=0
LDFLAGS := -pie -Wl,-z,relro,-z,now

all: chall

chall: chall.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

clean:
	rm -f chall
.PHONY: all clean
