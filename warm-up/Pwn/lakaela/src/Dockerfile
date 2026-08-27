FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    libc6 \
    libc-bin \
    libc6-dev \
    gcc \
    make \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY chall.c Makefile ./
RUN make clean && make

FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    libc6 \
    libc-bin \
    socat \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -M -s /usr/sbin/nologin ctf \
    && mkdir -p /home/ctf \
    && chown root:root /home/ctf \
    && chmod 0555 /home/ctf

WORKDIR /home/ctf
COPY --from=builder /build/chall /home/ctf/chall
COPY run.sh /home/ctf/run.sh
COPY flag.txt /flag.txt

RUN chown root:root /home/ctf/chall /home/ctf/run.sh /flag.txt \
    && chmod 0555 /home/ctf/chall /home/ctf/run.sh \
    && chmod 0444 /flag.txt

EXPOSE 31337
CMD ["/home/ctf/run.sh"]
