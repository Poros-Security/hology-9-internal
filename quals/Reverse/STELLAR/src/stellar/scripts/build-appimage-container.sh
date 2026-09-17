#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
uid="$(id -u)"
gid="$(id -g)"

docker run --rm --network host \
  -e APPIMAGE_EXTRACT_AND_RUN=1 \
  -v "$repo_dir:/source:ro" \
  -v "$repo_dir/release:/output" \
  -v stellar-cargo-registry:/root/.cargo/registry \
  -v stellar-cargo-git:/root/.cargo/git \
  -v stellar-appimage-target:/build/stellar/src-tauri/target \
  ubuntu:22.04 bash -lc "
    set -euo pipefail
    export DEBIAN_FRONTEND=noninteractive
    apt-get -o Acquire::ForceIPv4=true update -qq
    apt-get -o Acquire::ForceIPv4=true install -y --no-install-recommends \
      build-essential ca-certificates curl file libwebkit2gtk-4.1-dev \
      libappindicator3-dev librsvg2-dev patchelf pkg-config libssl-dev \
      libxdo-dev xz-utils

    mkdir -p /build/stellar
    tar -C /source \
      --exclude='./node_modules' \
      --exclude='./target' \
      --exclude='./src-tauri/target' \
      --exclude='./dist' \
      --exclude='./release' \
      --exclude='./organizer-analysis' \
      --exclude='./.hallmark' \
      --exclude='./WhatsApp Image 2026-09-17 at 09.55.59.jpeg' \
      -cf - . | tar -C /build/stellar -xf -

    cd /tmp
    curl --proto '=https' --tlsv1.2 -fsSLO \
      https://nodejs.org/dist/v22.14.0/node-v22.14.0-linux-x64.tar.xz
    curl --proto '=https' --tlsv1.2 -fsSLO \
      https://nodejs.org/dist/v22.14.0/SHASUMS256.txt
    grep ' node-v22.14.0-linux-x64.tar.xz\$' SHASUMS256.txt | sha256sum -c -
    tar -C /opt -xf node-v22.14.0-linux-x64.tar.xz
    export PATH=/opt/node-v22.14.0-linux-x64/bin:/root/.cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | \
      sh -s -- -y --default-toolchain 1.88.0 --profile minimal --target x86_64-unknown-linux-gnu
    . /root/.cargo/env

    cd /build/stellar
    echo \"Build baseline: \$(. /etc/os-release; echo \"\$PRETTY_NAME\")\"
    ldd --version | head -1
    rustc -V
    node -v
    pkg-config --modversion webkit2gtk-4.1 gtk+-3.0
    npm ci
    npm run tauri -- build --bundles appimage

    artifact=\$(find src-tauri/target/release/bundle/appimage -maxdepth 1 -type f -name '*.AppImage' -print -quit)
    test -n \"\$artifact\"
    install -m 0755 \"\$artifact\" /output/STELLAR.AppImage
    chown $uid:$gid /output/STELLAR.AppImage
  "
