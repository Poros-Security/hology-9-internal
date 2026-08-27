#!/bin/sh
set -eu

: "${GZCTF_FLAG:?GZCTF_FLAG not set}"
printf "%s\n" "$GZCTF_FLAG" > /tmp/flag.txt
chmod 444 /tmp/flag.txt

exec socat TCP-LISTEN:1000,reuseaddr,fork EXEC:"/home/ctf/chall/chall",stderr
