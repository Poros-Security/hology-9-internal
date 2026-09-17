#!/bin/sh

set -eu

CHALL_DIR="/home/ctf/chall/src"
FLAG_FILE="$CHALL_DIR/flag.txt"

if [ -z "${GZCTF_FLAG:-}" ]; then
    GZCTF_FLAG='HOLOGY9{Great_Thief_local_test_flag}'
fi

printf '%s\n' "$GZCTF_FLAG" > "$FLAG_FILE"

chown root:ctf "$FLAG_FILE"
chmod 440 "$FLAG_FILE"

exec su -s /bin/sh ctf -c "exec socat \
    TCP-LISTEN:8011,reuseaddr,fork \
    EXEC:\"$CHALL_DIR/chall\",chdir=\"$CHALL_DIR\",stderr"