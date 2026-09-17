#!/bin/sh
set -eu

[ "$#" = 1 ] || {
    echo "usage: run_engine.sh CONFIG" >&2
    exit 64
}

exec /opt/OpenTee/bin/opentee-engine -c "$1" -f
