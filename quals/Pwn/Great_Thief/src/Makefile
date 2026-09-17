CC      := gcc
CFLAGS  := -fno-stack-protector -no-pie -z norelro -z noexecstack -w
TARGET  := chall
SRC     := chall.c

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) $(SRC) -o $(TARGET)

run: $(TARGET)
	chmod +x run.sh
	./run.sh

docker-build:
	docker build -t chall-thief .

docker-run:
	docker run --rm -p 8011:8011 -e GZCTF_FLAG="$(FLAG)" chall-thief

clean:
	rm -f $(TARGET)

.PHONY: all run docker-build docker-run clean