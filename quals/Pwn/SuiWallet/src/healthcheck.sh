#!/bin/sh
set -eu
printf 'session\nquit\n' | nc -w 5 127.0.0.1 9999 >/dev/null
