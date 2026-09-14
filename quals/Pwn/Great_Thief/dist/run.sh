#!/bin/sh
export FLAG=${GZCTF_FLAG}
socat tcp-l:8011,reuseaddr,fork exec:"stdbuf -o0 /home/ctf/chall/src/chall"
