CC      := gcc
CFLAGS  := -Wall -Wextra -O0 -fno-stack-protector -no-pie -z norelro
TARGET  := ret2ret2ret2

all: $(TARGET)

$(TARGET): vuln.c
	$(CC) $(CFLAGS) vuln.c -o $(TARGET)

clean:
	rm -f $(TARGET)
