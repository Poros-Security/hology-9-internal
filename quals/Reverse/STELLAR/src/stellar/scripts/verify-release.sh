#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"
binary=release/STELLAR
for artifact in release/*; do
  case "$(basename "$artifact")" in
    STELLAR|challenge.txt|SHA256SUMS) ;;
    *) echo "unexpected release artifact: $artifact" >&2; exit 1 ;;
  esac
done
test -x "$binary"
file "$binary" | tee /dev/stderr | grep -q 'ELF 64-bit LSB pie executable'
readelf -h "$binary" | grep -q 'Type:.*DYN'
readelf -d "$binary" | grep -q 'NEEDED'
if readelf -S "$binary" | grep -Eq '\.debug_(info|line|str)'; then echo 'DWARF sections found' >&2; exit 1; fi
if strings "$binary" | grep -F 'HOLOGY9{' | grep -Fv 'HOLOGY9{production_flag_here'; then echo 'non-decoy plaintext flag leak in ELF' >&2; exit 1; fi
if grep -R -a -F 'HOLOGY9{' dist; then echo 'plaintext flag leak in frontend bundle' >&2; exit 1; fi
if nm "$binary" 2>&1 | grep -v 'no symbols' | grep -q 'stellar_gif'; then echo 'challenge symbols were not stripped' >&2; exit 1; fi
solver_frame="$(mktemp --suffix=.ppm)"
trap 'rm -f "$solver_frame"' EXIT
cargo run --locked --release -p author-solver -- "$binary" "$solver_frame"
file "$solver_frame" | grep -q 'Netpbm image data'
sha256sum release/STELLAR release/challenge.txt > release/SHA256SUMS
echo 'release verification passed'
