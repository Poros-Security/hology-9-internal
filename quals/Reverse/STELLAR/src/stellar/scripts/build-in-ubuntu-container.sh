#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
uid="$(id -u)"
gid="$(id -g)"
docker run --rm --network host -v "$repo_dir:/work" -w /work ubuntu:24.04 bash -lc "
  set -euo pipefail
  export DEBIAN_FRONTEND=noninteractive
  apt-get -o Acquire::ForceIPv4=true update -qq
  apt-get -o Acquire::ForceIPv4=true install -y --no-install-recommends \
    build-essential ca-certificates curl file libwebkit2gtk-4.1-dev \
    libappindicator3-dev librsvg2-dev patchelf pkg-config libssl-dev libxdo-dev xz-utils
  cd /tmp
  curl --proto '=https' --tlsv1.2 -fsSLO \
    https://nodejs.org/dist/v22.14.0/node-v22.14.0-linux-x64.tar.xz
  curl --proto '=https' --tlsv1.2 -fsSLO \
    https://nodejs.org/dist/v22.14.0/SHASUMS256.txt
  grep ' node-v22.14.0-linux-x64.tar.xz$' SHASUMS256.txt | sha256sum -c -
  tar -C /opt -xf node-v22.14.0-linux-x64.tar.xz
  export PATH=/opt/node-v22.14.0-linux-x64/bin:/root/.cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | \
    sh -s -- -y --default-toolchain 1.88.0 --profile minimal --target x86_64-unknown-linux-gnu
  . /root/.cargo/env
  cd /work
  rustc -V && cargo -V
  node -v && npm -v
  gcc --version | head -1
  ld --version | head -1
  pkg-config --modversion gtk+-3.0 webkit2gtk-4.1
  npm ci
  npm run build
  cargo build --locked --release --features custom-protocol \
    --target x86_64-unknown-linux-gnu --manifest-path src-tauri/Cargo.toml
  chown -R $uid:$gid /work/src-tauri/target
"
