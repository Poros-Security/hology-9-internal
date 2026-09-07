FROM dimasmaualana/eth:latest

ENV LAUNCHER_PORT=5000
ENV DISABLE_TICKET=true

COPY deploy/ /home/ctf/
COPY .env /home/ctf/.env

COPY contracts /tmp/contracts

RUN true \
    && cd /home/ctf \
    && pip install -r requirements.txt --break-system-packages \
    && cd /tmp \
    && forge build --out /home/ctf/compiled \
    && rm -rf /tmp/contracts \
    && true
