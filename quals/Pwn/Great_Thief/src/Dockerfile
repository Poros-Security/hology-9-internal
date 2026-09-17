FROM debian:trixie-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends socat \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1001 -s /bin/sh ctf
RUN mkdir -p /home/ctf/chall/src

COPY ./chall /home/ctf/chall/src/chall
COPY ./run.sh /home/ctf/chall/src/run.sh

RUN chown -R root:ctf /home/ctf/chall \
    && chmod 550 /home/ctf/chall/src \
    && chmod 550 /home/ctf/chall/src/chall \
    && chmod 550 /home/ctf/chall/src/run.sh

WORKDIR /home/ctf/chall/src
CMD ["./run.sh"]