FROM ubuntu:24.04

RUN apt-get update \
    && apt-get install -y --no-install-recommends libc6 libc-bin \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /challenge
COPY chall /challenge/chall

RUN chmod 0555 /challenge/chall

ENTRYPOINT ["/challenge/chall"]
