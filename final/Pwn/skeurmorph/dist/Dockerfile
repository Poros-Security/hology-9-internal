FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    gcc \
    socat \
    libc6 \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash ctf

WORKDIR /home/ctf

COPY chall.c .
COPY run.sh .

RUN gcc -o filekeeper chall.c \
    -no-pie \
    -Wl,-z,relro,-z,now \
    -O0 \
    && chmod 755 filekeeper \
    && chmod +x run.sh


RUN cp /lib/x86_64-linux-gnu/libc.so.6 /home/ctf/libc.so.6 \
    && cp /lib/x86_64-linux-gnu/ld-linux-x86-64.so.2 /home/ctf/ld.so

EXPOSE 9001

USER ctf

CMD ["./run.sh"]
