#!/bin/sh
set -eu

printf '%s\n' "${GZCTF_FLAG:-HIBCHB26{P3m4loe_f0rg3d_th3_w4t3r_h0us3_placeholder}}" > /flag.txt
chown root:root /flag.txt
chmod 0444 /flag.txt

cd /home/ctf
exec socat -T 60 TCP-LISTEN:31337,reuseaddr,fork EXEC:"/home/ctf/chall",stderr,su=ctf
