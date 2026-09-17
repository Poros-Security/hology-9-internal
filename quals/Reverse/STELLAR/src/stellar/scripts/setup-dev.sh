#!/usr/bin/env bash
set -euo pipefail

if ! grep -q 'Ubuntu 24.04' /etc/os-release; then
  echo 'warning: the release reference is Ubuntu 24.04.4 LTS; this host differs' >&2
fi
sudo apt-get update
sudo apt-get install -y build-essential curl file libwebkit2gtk-4.1-dev libappindicator3-dev \
  librsvg2-dev patchelf pkg-config libssl-dev libxdo-dev
if command -v rustup >/dev/null 2>&1; then
  rustup toolchain install 1.88.0 --profile minimal --target x86_64-unknown-linux-gnu
else
  echo 'rustup not found; using the system Rust toolchain for development.' >&2
  echo 'Organizer release builds should still use the documented Rust 1.88.0 reference environment.' >&2
fi
echo 'Install Node.js 22.14.0 and npm 10.9.2, then run scripts/build-development.sh.'
