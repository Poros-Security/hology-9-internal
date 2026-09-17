FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends python3 xinetd \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin ctf

WORKDIR /app
COPY challenge.py policy.py tickets.py flag.txt /app/
COPY xinetd.conf /etc/xinetd.conf
RUN chmod 0555 /app && chmod 0444 /app/*.py /app/flag.txt /etc/xinetd.conf

EXPOSE 1337/tcp
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python3 -c "import socket; s=socket.create_connection(('127.0.0.1',1337),2); assert b'S U I T E L' in s.recv(4096); s.close()"
CMD ["/usr/sbin/xinetd", "-dontfork", "-f", "/etc/xinetd.conf"]
