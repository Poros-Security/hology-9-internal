#!/bin/sh
set -eu
. /etc/suiwallet/runtime.conf

work=$(mktemp -d /tmp/suiwallet.XXXXXX)
engine_pid=
in_bridge_pid=
out_bridge_pid=

cleanup() {
    if [ -n "$in_bridge_pid" ] && kill -0 "$in_bridge_pid" 2>/dev/null; then
        kill "$in_bridge_pid" 2>/dev/null || true
        wait "$in_bridge_pid" 2>/dev/null || true
    fi
    if [ -n "$out_bridge_pid" ] && kill -0 "$out_bridge_pid" 2>/dev/null; then
        kill "$out_bridge_pid" 2>/dev/null || true
        wait "$out_bridge_pid" 2>/dev/null || true
    fi
    if [ -n "$engine_pid" ] && kill -0 "$engine_pid" 2>/dev/null; then
        kill "$engine_pid" 2>/dev/null || true
        wait "$engine_pid" 2>/dev/null || true
    fi
    rm -rf "$work"
}
trap cleanup EXIT HUP INT TERM

exec 8<&0
exec 9>&1

mkdir -p "$work/tas" "$work/storage"
install -m 0444 /opt/suiwallet/"$TA_NAME" "$work/tas/$TA_NAME"
mkfifo "$work/player.in" "$work/player.out"
( cat <&8 >"$work/player.in" ) &
in_bridge_pid=$!
( cat "$work/player.out" >&9 ) &
out_bridge_pid=$!

cat > "$work/engine.conf" <<EOF
[PATHS]
ta_dir_path = $work/tas
core_lib_path = $OPEN_TEE_PREFIX/lib
subprocess_manager = libManagerApi.so
subprocess_launcher = libLauncherApi.so
EOF

export OPENTEE_SOCKET_FILE_PATH="$work/opentee.sock"
export OPENTEE_STORAGE_PATH="$work/storage"
export I="$work/player.in"
export O="$work/player.out"
export LD_LIBRARY_PATH="$OPEN_TEE_PREFIX/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

/usr/local/bin/run_engine.sh "$work/engine.conf" &
engine_pid=$!

for _ in $(seq 1 50); do
    [ -S "$OPENTEE_SOCKET_FILE_PATH" ] && break
    sleep 0.1
done
[ -S "$OPENTEE_SOCKET_FILE_PATH" ] || {
    echo "Open-TEE socket did not appear" >&2
    exit 1
}

timeout --foreground -k 5 "$TIMEOUT" "$HOST_BIN"
