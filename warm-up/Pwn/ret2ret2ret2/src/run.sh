#!/bin/sh
set -eu

: "${GZCTF_FLAG:=HIBCHB26{ret2ret2ret2_local_test_flag}}"
printf "%s\n" "$GZCTF_FLAG" > /tmp/flag
chmod 444 /tmp/flag

exec socat TCP-LISTEN:9999,reuseaddr,fork EXEC:"/home/ctf/chall/ret2ret2ret2",stderr
