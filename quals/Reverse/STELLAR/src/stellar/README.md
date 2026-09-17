# STELLAR

STELLAR is a Linux x86-64 reverse-engineering challenge presented as an
unofficial Hoshimachi Suisei fan archive. The interface is a fan-first artist
site: profile, music, gallery, highlights, and properly attributed sources.
The development media set includes official-site imagery and community-hosted
GIFs; review every asset's permission and attribution before public release.

Every GIF in the archive is encrypted into an opaque tagged record and embedded
in the main Tauri ELF. When the frontend
requests an animation, the modified Tauri asset layer opens that record, passes
the recovered GIF through the manual decoder, and returns a private binary frame
container for canvas playback. Asset paths are opaque tokens instead of source
filenames. The carrier includes an encrypted raster and encrypted VM program.
After a full loop plus a pause/resume gesture, the playback-state token decrypts
that program and transforms the raster into a visible flag frame.

There are no commands, sidecars, network services, anti-debugging checks,
packers, machine identifiers, address-derived values, or multi-stage flag
fragments.

## Pinned reference environment

Final release builds target **Ubuntu 22.04 LTS (x86-64, glibc 2.35)** and are
tested on Ubuntu 22.04 and 24.04. Building on this older baseline prevents the
AppImage from inheriting rolling-distribution glibc requirements.

| Component | Pinned/tested version |
|---|---:|
| Rust / Cargo | 1.88.0 / 1.88.0 |
| Tauri | 2.8.5 (local `2.8.5-stellar.1` facade) |
| tauri-build / CLI | 2.4.1 / 2.8.4 |
| Node.js / npm | 22.14.0 / 10.9.2 |
| WebKitGTK | Ubuntu 22.04 update (`libwebkit2gtk-4.1`) |
| GTK | Ubuntu 22.04 update (`libgtk-3`) |
| glibc | 2.35 |
| GCC / GNU binutils | Ubuntu 22.04 defaults |

Capture the container build versions with `rustc -Vv`, `cargo -V`, `node -v`,
`npm -v`, `gcc --version`, `ld --version`, and
`pkg-config --modversion webkit2gtk-4.1 gtk+-3.0` in the organizer build log.
Rustup is optional for local development when a sufficiently recent system
Rust compiler is installed. It remains the simplest way to reproduce the exact
Rust 1.88.0 organizer toolchain. `make appimage` performs the release compile
and AppImage deployment inside `ubuntu:22.04`; do not package releases directly
on Kali or another rolling distribution.

## Change the GIF collection

The collection is data-driven. You can replace the supplied animations with any
valid GIF87a/GIF89a files, including animations with different dimensions,
palettes, frame counts, delays, transparency, interlacing, and disposal modes.

1. Put the files in `app/src/assets/gifs/`.
2. Add its visitor-facing title, caption, credit, and source at the matching
   sorted position in `mediaCopy` in `app/src/lib/suisei-content.ts`. Additional
   files still work and receive a neutral fallback caption.
3. Choose which filename carries the encrypted flag raster with
   `STELLAR_FLAG_GIF`. It defaults to `midnight-comet.gif`.
4. Run the builder.

```bash
export STELLAR_FLAG='HOLOGY9{Fake_flag_dont_submit}'
export STELLAR_FLAG_GIF='my-special-animation.gif'
cargo run --locked -p midnight-builder -- app/src/assets/gifs
```

The builder validates every GIF, appends an encrypted visual frame only to the
selected carrier in memory, encrypts its small VM program, encrypts every GIF
into token-named `app/src/assets/vault/*.stlr` records, and regenerates both
registries. The source GIFs
remain ordinary, viewer-compatible files and do not receive the flag. The flag
is rasterized during generation and is never stored as a plaintext string.

Use `--generate-defaults` only when you intentionally want to replace the folder
with the procedural sample collection.

## Development

```bash
scripts/setup-dev.sh
scripts/build-development.sh
scripts/build-in-ubuntu-container.sh
cargo run -p animation-tester -- app/src/assets/gifs/midnight-comet.gif /tmp/stellar-frames
cargo run --release -p author-solver -- release/STELLAR revealed.ppm
```

The default development value is `HOLOGY9{Fake_flag_dont_submit}`. Produce an
organizer release only with an injected production value:

```bash
export STELLAR_FLAG='HOLOGY9{production_value_here}'
export STELLAR_FLAG_GIF='midnight-comet.gif'
make appimage
```

The resulting player package is `release/STELLAR.AppImage`. Run `make verify`
to extract it and re-run the inner-ELF, leak, and independent-solver checks.

The production flag is consumed only by `midnight-builder`; the application
build starts after the environment variable is unset. Plaintext must be absent
from Rust/TypeScript release state, the JS bundle, source GIFs, and the stripped
ELF. The release verifier runs the independent solver against the finished ELF.

## Framework boundary

The local crate named `tauri` re-exports exact upstream Tauri 2.8.5 and adds one
asset feature: the opaque embedded-animation resolver, playback-state gate,
visual VM, and native frame pipeline. The application shell remains ordinary. Normal
Tauri/GTK/WebKitGTK behavior remains upstream behavior.

Do not ship `tools/`, `patches/`, source, source maps, Cargo artifacts, this
README, `design.md`, or Hallmark metadata to players. Ship only
`release/STELLAR.AppImage`, `release/challenge.txt`, checksums, and the documented Ubuntu
runtime requirements.

`challenge/playtest-plan.md` remains a mandatory organizer gate. A human
external playtest cannot be inferred from automated tests.
