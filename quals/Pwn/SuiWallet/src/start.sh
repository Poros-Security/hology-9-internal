#!/bin/sh
set -eu
flag_value=${GZCTF_FLAG:-}
if [ -z "$flag_value" ]; then
    flag_value='CTF{remote_flag_placeholder}'
fi
flag_hash=$(printf '%s\n' "$flag_value" | sha256sum | cut -d' ' -f1)
flag_path="/flag-${flag_hash}.txt"
rm -f /flag /flag-*.txt
printf '%s\n' "$flag_value" > "$flag_path"
unset GZCTF_FLAG
chown suiwallet:suiwallet "$flag_path"
chmod 0400 "$flag_path"
mkdir -p /var/run/xinetd
exec /usr/sbin/xinetd -dontfork -f /etc/xinetd.conf
