#!/bin/sh

set -eu

exec /usr/local/bin/ynetd \
    -p 8013 \
    /usr/local/bin/python3 \
    -u \
    /home/ctf/chall/chall.py
