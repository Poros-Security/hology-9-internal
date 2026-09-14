FROM node:24-slim AS ui
WORKDIR /ui
COPY ui/package.json ui/package-lock.json ./
RUN npm ci
COPY ui ./
RUN npx ng build

FROM node:22-slim AS deps
WORKDIR /api
COPY api/package.json api/package-lock.json ./
RUN npm ci --omit=dev

FROM node:22-slim
WORKDIR /app
ENV NODE_ENV=production
ENV DB_PATH=/var/lib/ledger/ledger.db

COPY docker/entrypoint.sh /usr/local/bin/entrypoint
COPY api ./
COPY --from=deps /api/node_modules ./node_modules
COPY --from=ui /ui/dist/ui/browser ./public

RUN chmod +x /usr/local/bin/entrypoint && mkdir -p /var/lib/ledger

EXPOSE 3000
ENTRYPOINT ["entrypoint"]
