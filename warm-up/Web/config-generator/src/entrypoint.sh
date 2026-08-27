#!/bin/sh

RANDOM_STR=$(cat /dev/urandom | tr -dc 'a-f0-9' | fold -w 32 | head -n 1)
if [ -n "$GZCTF_FLAG" ]; then
    echo "$GZCTF_FLAG" > /flag-${RANDOM_STR}.txt
    chmod 444 /flag-${RANDOM_STR}.txt
fi
exec "$@"