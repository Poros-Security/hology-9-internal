FROM rust:1-slim-bookworm AS build
RUN apt-get update && apt-get install -y --no-install-recommends gcc binutils \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY src/main.rs src/notes.c ./src/

RUN gcc -O1 -fno-stack-protector -c src/notes.c -o notes.o \
    && ar rcs libnotes.a notes.o \
    && rustc -O -C link-args=-no-pie -L . -l static=notes -o safenotes src/main.rs

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends socat \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m ctf
WORKDIR /home/ctf
COPY --from=build /src/safenotes ./safenotes
COPY flag.txt ./flag.txt
RUN chmod 555 ./safenotes && chmod 444 ./flag.txt && chown -R root:root /home/ctf

USER ctf
EXPOSE 1111
CMD ["socat", "-T60", "TCP-LISTEN:1111,reuseaddr,fork", "EXEC:./safenotes,stderr"]
