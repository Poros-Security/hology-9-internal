#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"
for artifact in release/STELLAR release/STELLAR.AppImage release/challenge.txt release/SHA256SUMS; do
  if [[ -f "$artifact" ]]; then rm -- "$artifact"; fi
done
echo 'removed generated files from release/ (source and build trees were preserved)'
