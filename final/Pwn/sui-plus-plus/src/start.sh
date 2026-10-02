#!/bin/sh
set -eu

# GZCTF injects one team-specific flag into each Dynamic Container instance.
# Keep the checked-in flag.txt as the local fallback when the variable is absent.
if [ -n "${GZCTF_FLAG:-}" ]; then
    printf '%s\n' "$GZCTF_FLAG" > /home/ctf/flag.txt
fi

exec socat TCP-LISTEN:1337,reuseaddr,fork EXEC:/home/ctf/suipp,stderr
