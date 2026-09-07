#!/bin/sh
set -e

RAND=$(od -A n -t x1 -N 6 /dev/urandom | tr -d ' \n')
FLAG_PATH="/flag_${RAND}.txt"

echo "${GZCTF_FLAG:-${FLAG:-HOLOGY9{dummy_flag_for_local_testing}}}" > "$FLAG_PATH"

exec node /app/src/app.js
