FROM debian:trixie-slim AS build

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc make libc6-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY chall.c Makefile ./
RUN make

FROM debian:trixie-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends socat \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1001 -s /bin/sh ctf

WORKDIR /home/ctf/chall
COPY --from=build /build/chall ./chall
COPY run.sh ./run.sh

RUN chown -R root:root /home/ctf/chall \
    && chmod 555 /home/ctf/chall /home/ctf/chall/run.sh /home/ctf/chall/chall
USER ctf
EXPOSE 1000
CMD ["./run.sh"]
