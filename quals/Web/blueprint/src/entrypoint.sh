#!/bin/sh
set -eu

FLAG_VALUE="${GZCTF_FLAG:-${FLAG:-HOLOGY9{local_dev_flag}}}"
RAND="$(od -A n -t x1 -N 6 /dev/urandom | tr -d ' \n')"
FLAG_REAL_PATH="/flag_${RAND}.txt"

printf '%s\n' "$FLAG_VALUE" > "$FLAG_REAL_PATH"
chown appuser:appuser "$FLAG_REAL_PATH"
chmod 400 "$FLAG_REAL_PATH"
rm -f /opt/app/secret/flag.txt
ln -s "$FLAG_REAL_PATH" /opt/app/secret/flag.txt

pg_ctlcluster 15 main start

if ! gosu postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname = 'taskforge'" | grep -q 1; then
  gosu postgres psql -c "CREATE ROLE taskforge LOGIN PASSWORD 'taskforge';"
fi

gosu postgres psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'taskforge';" >/dev/null
gosu postgres psql -c "DROP DATABASE IF EXISTS taskforge;" >/dev/null
gosu postgres psql -c "CREATE DATABASE taskforge OWNER taskforge;" >/dev/null
gosu postgres psql -d taskforge -f /opt/app/src/api/db/init.sql >/dev/null

export JWT_SECRET="${JWT_SECRET:-$(od -A n -t x1 -N 32 /dev/urandom | tr -d ' \n')}"

exec gosu appuser node /opt/app/src/api/index.js
