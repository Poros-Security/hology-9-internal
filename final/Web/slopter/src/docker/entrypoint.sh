#!/bin/sh
set -e

if [ -z "$GZCTF_FLAG" ]; then
    echo "GZCTF_FLAG is not set" >&2
    exit 1
fi

exec supervisord -c /etc/supervisord.conf
