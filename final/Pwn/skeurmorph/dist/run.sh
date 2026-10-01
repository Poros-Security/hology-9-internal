#!/bin/sh

echo "${GZCTF_FLAG:-HOLOGY9{test_flag}}" > /tmp/flag.txt
chmod 444 /tmp/flag.txt

socat tcp-l:9001,reuseaddr,fork exec:"./filekeeper",stderr
