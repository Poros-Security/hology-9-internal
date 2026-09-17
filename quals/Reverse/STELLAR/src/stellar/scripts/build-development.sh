#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"
export STELLAR_FLAG="${STELLAR_FLAG:-HOLOGY9{Fake_flag_dont_submit}}"
cargo run --locked -p midnight-builder -- app/src/assets/gifs
npm ci
npm run build
cargo build --locked --manifest-path src-tauri/Cargo.toml
echo "Development binary: src-tauri/target/debug/STELLAR"
