#!/usr/bin/env bash
set -euo pipefail

challenge_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
appimage="${1:-$challenge_dir/dist/STELLAR.AppImage}"
output="${2:-$challenge_dir/solver/revealed.ppm}"
extract_dir="$(mktemp -d)"
trap 'rm -rf -- "$extract_dir"' EXIT

(
  cd "$extract_dir"
  "$appimage" --appimage-extract >/dev/null
)

cargo run --release --manifest-path "$challenge_dir/solver/Cargo.toml" -- \
  "$extract_dir/squashfs-root/usr/bin/STELLAR" "$output"
echo "Open $output to read the flag."
