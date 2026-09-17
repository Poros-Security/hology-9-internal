#!/bin/sh
set -eu

flag_value=${GZCTF_FLAG:-}
if [ -z "$flag_value" ]; then
    flag_value='HOLOGY9{local_suicar_dynamic_test_flag}'
fi

printf '%s\n' "$flag_value" > /flag
chmod 0444 /flag
unset GZCTF_FLAG

exec /usr/sbin/xinetd -dontfork
