#!/bin/sh
set -e

if [ -z "$GZCTF_FLAG" ]; then
    echo "GZCTF_FLAG is not set" >&2
    exit 1
fi

rm -f "$DB_PATH" "$DB_PATH-wal" "$DB_PATH-shm"
node seed.js

exec node server.js
