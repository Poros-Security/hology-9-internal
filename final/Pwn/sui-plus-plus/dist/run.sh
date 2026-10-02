#!/bin/sh
set -eu

if [ -n "${GZCTF_FLAG:-}" ]; then
    printf '%s\n' "$GZCTF_FLAG" > /home/ctf/flag.txt
fi

exec socat TCP-LISTEN:1337,reuseaddr,fork EXEC:/home/ctf/suipp,stderr
