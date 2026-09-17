#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"
appimage=release/STELLAR.AppImage

for artifact in release/*; do
  case "$(basename "$artifact")" in
    STELLAR.AppImage|challenge.txt|SHA256SUMS) ;;
    *) echo "unexpected release artifact: $artifact" >&2; exit 1 ;;
  esac
done

test -x "$appimage"
file "$appimage" | tee /dev/stderr | grep -q 'ELF 64-bit LSB pie executable'

extract_dir="$(mktemp -d)"
solver_frame="$(mktemp --suffix=.ppm)"
trap 'rm -rf -- "$extract_dir"; rm -f -- "$solver_frame"' EXIT
(
  cd "$extract_dir"
  "$repo_dir/$appimage" --appimage-extract >/dev/null
)
inner="$extract_dir/squashfs-root/usr/bin/STELLAR"
test -x "$inner"
file "$inner" | tee /dev/stderr | grep -q 'ELF 64-bit LSB pie executable'
readelf -h "$inner" | grep -q 'Type:.*DYN'
readelf -d "$inner" | grep -q 'NEEDED'

# The release baseline is Ubuntu 22.04 (glibc 2.35). AppImage deliberately
# does not bundle glibc, so reject any inner ELF or bundled library that was
# accidentally built against a newer host ABI.
highest_glibc="$({
  find "$extract_dir/squashfs-root" -type f -print0 | while IFS= read -r -d '' candidate; do
    if file -b "$candidate" | grep -q ELF; then
      readelf --version-info "$candidate" 2>/dev/null \
        | grep -o 'GLIBC_[0-9][0-9.]*' || true
    fi
  done
} | sort -Vu | tail -1)"
if [[ -z "$highest_glibc" ]] || \
   [[ "$(printf '%s\n' "$highest_glibc" GLIBC_2.35 | sort -V | tail -1)" != GLIBC_2.35 ]]; then
  echo "AppImage requires unsupported glibc version: ${highest_glibc:-unknown}" >&2
  exit 1
fi
echo "maximum bundled ABI requirement: $highest_glibc"

if readelf -S "$inner" | grep -Eq '\.debug_(info|line|str)'; then
  echo 'DWARF sections found in inner ELF' >&2
  exit 1
fi
if strings "$inner" | grep -F 'HOLOGY9{' | grep -Fv 'HOLOGY9{production_flag_here'; then
  echo 'non-decoy plaintext flag leak in inner ELF' >&2
  exit 1
fi
if grep -R -a -F 'HOLOGY9{' dist; then
  echo 'plaintext flag leak in frontend bundle' >&2
  exit 1
fi
cargo run --locked --release -p author-solver -- "$inner" "$solver_frame"
file "$solver_frame" | grep -q 'Netpbm image data'
sha256sum release/STELLAR.AppImage release/challenge.txt > release/SHA256SUMS
echo 'AppImage release verification passed'
