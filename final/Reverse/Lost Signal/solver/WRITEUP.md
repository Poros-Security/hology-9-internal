# Lost Signal — organizer solution, revision 7

**CONFIDENTIAL. This source, solver, writeup, and verification data stay out of
the player handouts.** Category: Reverse Engineering. Difficulty: Medium, with
light gameplay puzzles and simple final decryption.

## Overview and intended solve

The player explores five rooms in an abandoned facility. Four are locked and
their items form a progression chain. A stopped clock gives the generator code;
its drawer yields a storage key, Storage provides a reserve cell, and the robot
opens Observatory. A pass there opens Control. The observatory requires 15
matched signal inputs and fixes carrier C before the terminal captures an
encrypted archive and reveals its algorithm and ciphertext. It does not decrypt
or display the flag, key, IV or tag.

The human solve is:

1. Play until **Signal Captured**. Read **AES-256-GCM** and copy the ciphertext
   using **C** or **Copy Ciphertext**.
2. Identify Godot, extract the PCK, and follow `Terminal.archive_parameters()`.
3. Join Generator's `KEY_PART_1_HEX` then Robot's `KEY_PART_2_HEX` and XOR every byte with the visible
   `KEY_XOR_MASK = 0x6d`.
4. XOR each Observatory `IV_XOR_HEX` byte with `IV_XOR_MASK = 0x31`.
5. XOR each service-record `tag_xor_hex` byte with `TAG_XOR_MASK = 167`, written
   in decimal in `Terminal.gd`, to recover the tag;
   `aad:null` means no associated data.
6. Decrypt once with the captured ciphertext and print the flag. The reference
   solver takes 14 physical lines, including separate key parts, parameter recovery and blank lines.

The final decrypt requires no image reconstruction, cryptanalysis, brute force,
state-dependent key arithmetic, decompiler or native component. Ciphertext is
disguised on disk; the intended human solve obtains it through ordinary gameplay
without reversing that disguise.

![Wider facility](../verification/game/facility.png)

## Identify and extract

The executable reports Godot 4.5 and contains engine strings. The PCK starts with
ASCII `GDPC`; its header identifies Godot 4.5.0 and pack format v3. Scripts are
exported as readable `.gd` text. Scenes/textures are binary resources, but a
static solve does not need to convert them.

Use a Godot 4.5-compatible extractor. The upstream
[GDRE Tools documentation](https://github.com/GDRETools/gdsdecomp) describes these
commands:

```sh
gdre_tools --headless --extract=LostSignal.pck --output=extracted
```

Full recovery is useful if a participant wants to edit/run the project:

```sh
gdre_tools --headless --recover=LostSignal.pck --output=recovered
```

Organizers can reproduce extraction using the small included utility:

```sh
python tools/extract_pck.py dist/windows/LostSignal.pck extracted
```

That utility implements this unencrypted standalone PCK format and validates
resource checksums. It does not solve the challenge. Godot's
[PCK reader source](https://github.com/godotengine/godot/blob/4.5-stable/core/io/file_access_pack.cpp)
documents the format.

## Room puzzles and receiver progress

All four fields begin at zero. `Terminal.interact()` requires:

```text
power_phase      = 1
credential_band  = 1
keeper_code      = 1
carrier_slot     = 2
signal_inputs    = 15
```

| Object | Required interaction | Effect |
| --- | --- | --- |
| Loose fuse | Pick up | Adds ceramic fuse, ID `0x16` |
| Lobby clock | Read stopped time `03:15` | Clue for four-digit latch |
| Generator keypad | Enter `0315` | Opens Generator; other codes can be retried |
| Generator | Install fuse once | `power_phase = 1` |
| Generator tool drawer | Collect after power | Adds Storage key `0x42` |
| Generator floor | Optional pickup | Adds brass visitor badge `0x2b` |
| Storage key lock | Select Storage key and interact | Consumes key and opens Storage |
| Storage supply locker | Open once | Adds only reserve cell `0x39` |
| Maintenance robot | Install cell once | `keeper_code = 1`, opens Observatory |
| Observatory service locker | Open once | Adds only cracked service pass `0x65` |
| Control reader | Present selected service pass | `credential_band = 1`, opens Control |
| Observatory receiver | Match and submit 15 targets | `signal_inputs = 15`, fixes `carrier_slot = 2` |
| Terminal | Use with all conditions | Reveals algorithm and ciphertext |

The four closed doors have real collision and visible locked/open state. Each
unlock is permanent until restart; key use and pickups cannot duplicate items.
Critical pickups are deep enough inside their rooms to prevent interaction from
the other side of a closed doorway. Inventory never needs more than four slots.

The clock puzzle converts `03:15` to `0315`. Wrong codes leave the door closed
without resetting other progress. The tool drawer requires generator power.
The collectible Storage key is consumed by `DoorLock`; the AES key is assembled
separately from the Generator/Robot constants below.

At the receiver, E opens the calibration panel. A/D or Left/Right rotates the
current carrier; Enter/Space submits it. The panel shows both current and target
carrier and accepted sample count. The target sequence is:

```text
B A C C B A B C A C B B A B C
```

Every correct submit adds one sample; an incorrect input leaves the count
unchanged. Closing/reopening retains partial progress. Keyboard auto-repeat does
not count as a new submit. The 15th accepted input fixes carrier C; further tuning
and submits cannot change it or exceed 15. Choosing C before the 15th match is
insufficient to reveal CT. Restart resets the signal and relocks all rooms.

The sole decoy is the **Brass visitor badge**, ID `0x2b`. The reader rejects it
with “Visitor issue. This reader accepts service credentials.” It changes no
state and is never consumed. Selecting the cracked pass fixes the choice.

A normal route is fuse → clock → Generator keypad → generator → Storage key
→ Storage lock/locker → robot → Observatory pass → Control reader → 15 matched
receiver samples → Control terminal. Pass collection and receiver tuning can
be done in either order once Observatory opens. Opening the archive reveals only the
algorithm and ciphertext. The key, IV, tag and plaintext remain out of the UI.
The complete ciphertext spans three 52-character lines; copying produces one
156-character string without spaces or line breaks. Static reversing can still
skip gameplay if a participant reconstructs the disguised calibration data.

![Encrypted capture](../verification/game/capture.png)

![Receiver calibration](../verification/game/receiver.png)

![Fifteenth sample fixes carrier C](../verification/game/signal-locked.png)

## Follow the crypto references

`Terminal.gd` supplies the routing:

```gdscript
var key_part_1: PackedByteArray = get_node("../Generator").key_part_1()
var key_part_2: PackedByteArray = get_node("../Robot").key_part_2()
# AES-256 key = part 1 || part 2 (32 bytes); keep this order.
var key: PackedByteArray = key_part_1.duplicate()
key.append_array(key_part_2)
```

The order is **part 1 from Generator, then part 2 from Robot**, directly expressed
by names, comments and assembly above. Generator's `key_part_1()` restores bytes
0-15; Robot's `key_part_2()` restores bytes 16-31. Each hex-decodes its named
constant and XORs every byte with `KEY_XOR_MASK = 0x6d`. Both masks sit next to the
encoded data. There is no state or chain to carry across the two records.

Follow the dictionary in `Terminal.archive_parameters()`: the `key` field uses
the assembled bytes above, `iv` calls `Observatory.archive_iv()`, `tag` calls
`_restore_tag()` on `tag_xor_hex`, and `aad` reads JSON `null`. Those call sites
identify every crypto input and its decoding function. The participant does
not have to infer parameter roles from unlabeled hex or try different masks.

| Value | Location | Representation |
| --- | --- | --- |
| Key part 1, bytes 0–15 | `scripts/Generator.gd`, `KEY_PART_1_HEX` | 32 XOR-masked hex characters |
| Key part 2, bytes 16–31 | `scripts/Robot.gd`, `KEY_PART_2_HEX` | 32 XOR-masked hex characters |
| IV / nonce record | `scripts/Observatory.gd`, `IV_XOR_HEX` | 24 XOR-masked hex characters |
| Authentication tag record | `assets/archive/transmission.json`, `tag_xor_hex` | 32 XOR-masked hex characters |
| Ciphertext | Successful **Signal Captured** screen | 156 hex characters / 78 bytes |
| Associated data | JSON's `aad` | `null`, so Python uses `None` |

The encoded constants are:

```text
Key part 1: 5fec8130f3f84abd5bc8152321dd0223
Key part 2: 6298791a9e1a044ae1d4ee6de6a55de4
IV record:  c4aa7f60912989328f0da2b3
Tag record: 097d9005402ef0fa0229a661d8e116fa
```

Every parameter uses byte-wise XOR with an explicit constant. With zero-based `i`:

| Parameter | Forward encoding | Recovery |
| --- | --- | --- |
| Key | `e[i] = key[i] XOR 0x6d` | `key[i] = e[i] XOR 0x6d` |
| IV | `e[i] = iv[i] XOR 0x31` | `iv[i] = e[i] XOR 0x31` |
| Tag | `e[i] = tag[i] XOR 167` | `tag[i] = e[i] XOR 167` |

Follow `key_part_1()`, `key_part_2()`, `archive_iv()` and `Terminal._restore_tag()`
to read these inverses directly. Every recovery fits one Python comprehension.
Hex-decode records first, then XOR their bytes. `167` is a decimal integer,
equivalent to hex `0xa7`; its representation changes no arithmetic. Use the
literal as shown in the script rather than guessing its base or a hidden mask.

The full key is **32 bytes / 256 bits**, IV **12 bytes / 96 bits**, and tag
**16 bytes / 128 bits**. Decode hexadecimal into bytes; do not pass the printable
hex text as an AES key. Undo the small transforms before using AES. There is no
KDF, brute force or extra encryption key to find. Gameplay state does not alter
these parameters. Decoded values exist at runtime but are absent from player files.

The capture screen explicitly names **AES-256-GCM**. Captured ciphertext does
not include the tag. The Python `AESGCM` API accepts `ciphertext + tag`, verifies the tag, and
returns plaintext. Its
[official documentation](https://cryptography.io/en/46.0.3/hazmat/primitives/aead/#cryptography.hazmat.primitives.ciphers.aead.AESGCM)
describes that layout and authentication failure handling.

The ciphertext copied from the screen is:

```text
194d089b70f96522c805dfb2ae44b7917c54b1525340ee80af3e0b5e19364013a6bc797315941d293617bbb49de6be4feb2a59d5aee6c871a2901554891a2c371aba67674f664002b7a95976d5a6
```

## Short final solver

The reference solver contains ciphertext copied from gameplay, the encoded
records above, three one-line inverses and one authenticated-decryption call.
It does not extract the PCK; the participant first locates records and traces
the inverses in the readable scripts.

```python
"""Recover three masked parameters, then decrypt captured ciphertext."""
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

key_part_1_blob = bytes.fromhex("5fec8130f3f84abd5bc8152321dd0223")
key_part_2_blob = bytes.fromhex("6298791a9e1a044ae1d4ee6de6a55de4")
iv_blob = bytes.fromhex("c4aa7f60912989328f0da2b3")
tag_blob = bytes.fromhex("097d9005402ef0fa0229a661d8e116fa")
ct = bytes.fromhex("194d089b70f96522c805dfb2ae44b7917c54b1525340ee80af3e0b5e19364013a6bc797315941d293617bbb49de6be4feb2a59d5aee6c871a2901554891a2c371aba67674f664002b7a95976d5a6")

key = bytes(c ^ 0x6d for c in key_part_1_blob + key_part_2_blob)
iv = bytes(c ^ 0x31 for c in iv_blob)
tag = bytes(c ^ 167 for c in tag_blob)

print(AESGCM(key).decrypt(iv, ct + tag, None).decode())
```

Run from the organizer `challenge/` directory:

```sh
python -m pip install -r requirements-solver.txt
python solver/solve.py
```

Output:

```text
HOLOGY9{g3NeR4te_Fl4g_1deA_1s_S4m3_d1fFiCuL7y_t0_g3n3r4tE_g1T_cOm1t7_L0l_:V:V}
```

Case and punctuation are significant. `InvalidTag` means at least one input was
copied incorrectly; check key-part order and the explicit XOR constants,
ciphertext, and `None` AAD.

## Alternative approaches and fairness

The former `assets/archive/channel_09.bin` and JSON ciphertext path are removed.
`assets/receiver/calibration.dat` holds 512 samples. The generator masks each
ciphertext byte and scatters it into a different sample position; neither the
raw 78-byte ciphertext nor its complete hex representation is stored in a PCK
resource. `Observatory.read_transmission()` reverses this layout:

```text
position   = (73 + i * 149) & 511
correction = (0xb7 + i * 0x35 + (i >> 1) * 0x13) & 255
ct[i]      = samples[position] XOR correction       (i = 0..77)
```

`Terminal.interact()` calls it only after the original four progress conditions
and all 15 accepted signal inputs pass.
`captured_packet()` exposes only algorithm and restored ciphertext. The HUD
clears its capture/copy output on close, and a restart resets the terminal.

Participants can still reconstruct these samples statically, patch progress, or
instrument `captured_packet()` or `archive_parameters()`. These parameter
transforms and ciphertext masking are obfuscation to make a direct file search
less useful; it cannot force gameplay in a client-side reverse challenge. The
intended route remains play → capture CT → reverse key/IV/tag → AES-GCM decrypt.
Godot does not contain an in-game plaintext diagnostic or secret menu.

Every crypto input exists in the handout. State values gate gameplay only and
do not change the AES key. There are no internet services, timestamps, random
runtime values, anti-debug checks, or system-specific secrets.

The remaining reversing work is locating the correct object references,
recognizing three short byte transforms and recovering the standard crypto
parameters. Medium is a lighter design target
with light room puzzles and a standard final decrypt; no participant timing
trial was performed. The code, pixel assets, object logic, archive layout,
and story were authored for this
challenge, without reusing `flag-finder` implementation or assets.

See `verification/REPORT.md` and `handout-results.json` for final release evidence.
