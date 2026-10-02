FROM debian:stable-slim

RUN apt-get update && apt-get install -y --no-install-recommends socat \
    && groupadd --system ctf \
    && useradd --system --gid ctf --home-dir /home/ctf --create-home \
       --shell /usr/sbin/nologin ctf \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /home/ctf
COPY --chown=ctf:ctf suipp /home/ctf/suipp
COPY --chown=ctf:ctf flag.txt /home/ctf/flag.txt
COPY --chown=ctf:ctf start.sh /home/ctf/start.sh

USER ctf
EXPOSE 1337
CMD ["/bin/sh", "/home/ctf/start.sh"]
