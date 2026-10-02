FROM node:20-bookworm-slim

ENV PORT=8013 \
    NODE_ENV=production \
    DB_HOST=127.0.0.1 \
    DB_PORT=5432 \
    DB_NAME=ledger \
    DB_USER=ledger \
    DB_PASSWORD=ledger

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql postgresql-contrib gosu tini ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -r -u 1001 -s /usr/sbin/nologin appuser

WORKDIR /opt/app
COPY ./src/package.json ./src/package.json
RUN cd src && npm install --omit=dev \
    && npm cache clean --force

COPY ./src ./src
COPY ./entrypoint.sh ./entrypoint.sh

# Postgres tuning: this runs alongside Node in a single resource-capped
# container (~256M total), so keep shared_buffers/max_connections minimal.
RUN PGVER="$(ls /etc/postgresql)" \
    && CONF="/etc/postgresql/${PGVER}/main/postgresql.conf" \
    && sed -i "s/^max_connections = .*/max_connections = 20/" "$CONF" \
    && sed -i "s/^shared_buffers = .*/shared_buffers = 32MB/" "$CONF" \
    && printf '\nlisten_addresses = '"'"'127.0.0.1'"'"'\n' >> "$CONF"

RUN mkdir -p /opt/app/secret /run/postgresql \
    && chown -R postgres:postgres /var/lib/postgresql /run/postgresql \
    && chown -R root:root /opt/app \
    && chmod -R 555 /opt/app \
    && chmod 755 /opt/app/secret \
    && chmod 555 /opt/app/entrypoint.sh /opt/app/src/scripts/export.sh

EXPOSE 8013

ENTRYPOINT ["tini", "--", "/opt/app/entrypoint.sh"]
