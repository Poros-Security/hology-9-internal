#!/bin/sh
set -eu

flag="${GZCTF_FLAG:-}"
if [ -z "$flag" ]; then
  flag='HOLOGY9{local_flag}'
fi
printf '%s\n' "$flag" > /app/flag.txt
chmod 400 /app/flag.txt

exec ./mbg_server "${PORT:-7777}"
