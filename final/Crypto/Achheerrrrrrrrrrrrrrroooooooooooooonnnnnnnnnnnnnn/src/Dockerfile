FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y socat && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pycryptodome

WORKDIR /app
COPY chall.py .

RUN useradd -m ctf && chown -R ctf:ctf /app
USER ctf

EXPOSE 2000

CMD ["socat", "TCP-LISTEN:2000,reuseaddr,fork", "EXEC:python3 -u /app/chall.py,stderr"]