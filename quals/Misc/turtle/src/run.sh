#!/bin/sh

set -eu

exec /usr/local/bin/ynetd \
    -p 8011 \
    /usr/local/bin/python3 \
    -u \
    /home/ctf/chall/chall.py
