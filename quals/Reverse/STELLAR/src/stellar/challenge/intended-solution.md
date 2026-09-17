# STELLAR — intended organizer solution

Players receive the AppImage and `challenge.txt`. Extracting the AppImage yields
the stripped Tauri PIE at `squashfs-root/usr/bin/STELLAR`. The frontend requests
opaque hexadecimal asset tokens over the private URI scheme; source filenames
do not survive into the shipped registry or frontend bundle.

The embedded records begin with a non-printable 64-bit tag. The resolver
reconstructs that tag and the stream key from split constants. Recover this
layout from `open_asset` rather than searching for a readable magic string:

```text
tag:u64le
version:u8 = 3
reserved:[u8;3]
asset_id:u64le
nonce:u64le
gif_length:u32le
gif_crc32:u32le
program_length:u16le
reserved:u16le
encrypted_program[program_length]
ciphertext[gif_length]
```

The asset token is a reversible-looking one-way identifier derived from the
FNV-1a filename ID. The GIF cipher remains a small xorshift/add stream. Valid
records decrypt to ordinary GIF data and pass the stored CRC.

Most records contain only a one-byte no-op program. The carrier ends in a noisy
two-color frame and has a longer encrypted program. The browser does not request
the unlocked form immediately. It must observe a complete playback loop and a
user pause/resume gesture, then it mixes the decoded frame dimensions, delays,
rectangles, disposal modes, frame indices, and opaque asset token into a 64-bit
interaction key. It repeats the request with that key.

The native resolver independently calculates the expected key. A matching key
decrypts the carrier program and enters an eight-register VM:

```text
00              HALT
10 r imm32       MOVI r, imm32
20 r             XORSHIFT32 r
30 cursor state  REVEAL_PIXEL cursor, state
40 r imm32       ADDI r, imm32
50 lhs rhs rel16 JLT lhs, rhs, rel16
```

The program walks a rectangular raster in the final frame. Each decoded bit is
the low red-channel bit XORed with the current xorshift bit. VM output is cyan
or navy RGBA. Emulate the playback-state mixer, decrypt the bytecode, emulate
the VM, and save the final RGBA canvas. The production flag is readable only as
pixels in that image.

Several `HOLOGY9{production_flag_here...}` strings in VM trap messages are
decoys. There is no real plaintext flag, private GIF metadata flag, readable
vault signature, or source asset filename table.

Organizer verification:

```bash
cargo run --locked --release -p author-solver -- extracted-STELLAR revealed.ppm
```

Target solve time after this hardening is approximately three to five hours.
If external testing exceeds that because record discovery is too blind, add one
structural hint rather than restoring a printable magic value.
