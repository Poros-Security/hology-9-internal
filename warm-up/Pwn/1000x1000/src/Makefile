CC=gcc

CFLAGS=\
-O0 \
-no-pie \
-fno-stack-protector \
-fno-inline \
-Wall

LDFLAGS=\
-Wl,-z,relro,-z,now

all:
	$(CC) $(CFLAGS) chall.c -o chall $(LDFLAGS)

clean:
	rm -f chall