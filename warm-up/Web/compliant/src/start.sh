#!/bin/sh
set -eu

redis-server \
  --bind 127.0.0.1 \
  --protected-mode yes \
  --save "" \
  --appendonly no \
  --maxmemory 256mb \
  --maxmemory-policy noeviction &

exec bun run index.ts
