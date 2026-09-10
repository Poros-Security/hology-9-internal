FROM dimasmaualana/eth:latest

ENV LAUNCHER_PORT=5000
ENV DISABLE_TICKET=true
ENV EVM_VERSION=shanghai

COPY deploy/ /home/ctf/
COPY .env /home/ctf/.env

COPY contracts/ /tmp/contracts/
COPY foundry.toml /tmp/foundry.toml

RUN true \
    && cd /home/ctf \
    && pip install -r requirements.txt --break-system-packages \
    && cd /tmp \
    && forge build --root /tmp --contracts /tmp/contracts --out /home/ctf/compiled \
    && rm -rf /tmp/contracts /tmp/foundry.toml \
    && true

EXPOSE 5000
