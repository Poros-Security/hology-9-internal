FROM ubuntu:22.04

RUN useradd -m -s /bin/bash ctf

WORKDIR /app
COPY mbg_server .
COPY mbg.jpg .
COPY run.sh .

RUN chmod 555 mbg_server run.sh && \
    touch flag.txt && \
    chown ctf:ctf flag.txt && \
    chmod 600 flag.txt

USER ctf

EXPOSE 7777

CMD ["./run.sh"]
