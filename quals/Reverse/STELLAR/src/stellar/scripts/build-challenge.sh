#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"
: "${STELLAR_FLAG:?Set STELLAR_FLAG to the production HOLOGY9 flag}"
if [[ "$STELLAR_FLAG" == 'HOLOGY9{Fake_flag_dont_submit}' ]]; then
  echo 'refusing to produce a release with the development flag' >&2
  exit 1
fi
case "$STELLAR_FLAG" in HOLOGY9\{*\}) ;; *) echo 'STELLAR_FLAG has invalid format' >&2; exit 1;; esac

cargo run --locked --release -p midnight-builder -- app/src/assets/gifs
unset STELLAR_FLAG
npm ci
npm run build
cargo build --locked --release --features custom-protocol \
  --target x86_64-unknown-linux-gnu --manifest-path src-tauri/Cargo.toml
install -Dm755 src-tauri/target/x86_64-unknown-linux-gnu/release/STELLAR release/STELLAR
install -Dm644 challenge/challenge.txt release/challenge.txt
scripts/verify-release.sh
