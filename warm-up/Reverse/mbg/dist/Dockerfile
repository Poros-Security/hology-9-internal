FROM ubuntu:22.04

RUN useradd -m -s /bin/bash ctf

WORKDIR /app
COPY mbg_server .
COPY flag.txt .
COPY mbg.jpg .

RUN chmod +x mbg_server && \
    chown root:root flag.txt && \
    chmod 444 flag.txt

USER ctf

EXPOSE 7777

CMD ["./mbg_server", "7777"]
