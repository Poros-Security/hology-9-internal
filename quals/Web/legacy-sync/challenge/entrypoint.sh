#!/bin/sh
set -e

RAND=$(od -A n -t x1 -N 6 /dev/urandom | tr -d ' \n')
FLAG_PATH="/flag_${RAND}.txt"

echo "${FLAG:-HOLOGY9{placeholder_set_by_instancer}}" > "$FLAG_PATH"

exec node /app/src/app.js
