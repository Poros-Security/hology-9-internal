FROM python:3.13-slim

RUN apt-get update && apt-get install -y socat gcc && \
    pip install --no-cache-dir pycryptodome cysignals && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY chall.py .

EXPOSE 2000

CMD ["socat","TCP-LISTEN:2000,reuseaddr,fork","EXEC:python3 -u chall.py"]