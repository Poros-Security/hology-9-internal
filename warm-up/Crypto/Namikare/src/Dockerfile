FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install --no-install-recommends -y socat \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir libnum pycryptodome

RUN useradd --create-home --uid 10001 challenge

WORKDIR /home/challenge

COPY --chown=challenge:challenge server.py ./

USER challenge

EXPOSE 2000

CMD ["socat","TCP-LISTEN:2000,reuseaddr,fork","EXEC:python3 -u server.py,stderr"]
