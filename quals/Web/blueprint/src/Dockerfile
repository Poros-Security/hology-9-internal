FROM node:20-bookworm-slim

ENV PORT=8011 \
    NODE_ENV=production \
    DB_HOST=127.0.0.1 \
    DB_PORT=5432 \
    DB_NAME=taskforge \
    DB_USER=taskforge \
    DB_PASSWORD=taskforge

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql postgresql-contrib gosu tini ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -r -u 1001 -s /usr/sbin/nologin appuser

WORKDIR /opt/app
COPY ./api/package.json ./
RUN npm install --omit=dev \
    && npm cache clean --force

COPY ./api ./src/api
COPY ./ui ./src/ui
COPY ./entrypoint.sh ./entrypoint.sh

RUN mkdir -p /opt/app/secret /run/postgresql \
    && chown -R postgres:postgres /var/lib/postgresql /run/postgresql \
    && chown -R root:root /opt/app \
    && chmod -R 555 /opt/app \
    && chmod 755 /opt/app/secret \
    && chmod 555 /opt/app/entrypoint.sh /opt/app/src/api/scripts/maintenance.sh

EXPOSE 8011

ENTRYPOINT ["tini", "--", "/opt/app/entrypoint.sh"]
