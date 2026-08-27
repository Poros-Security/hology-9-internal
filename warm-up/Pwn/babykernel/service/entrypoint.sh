#!/bin/sh
set -eu

PORT="${PORT:-9999}"
/challenge/service/repack-rootfs.sh

echo "[entrypoint] babykernel listening on tcp/$PORT"
exec socat TCP-LISTEN:"$PORT",reuseaddr,fork EXEC:/challenge/service/run-qemu.sh,stderr,setsid,sigint
