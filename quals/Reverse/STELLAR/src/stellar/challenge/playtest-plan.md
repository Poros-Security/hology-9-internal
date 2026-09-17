# External playtest protocol

This checklist is an organizer gate, not a substitute for a human playtest.

Give a competent reverser a clean Ubuntu 24.04 VM containing only `STELLAR`,
`challenge.txt`, and the runtime package list. Record timestamps for framework
identification, encrypted-record discovery, stream-transform recovery, GIF
carving, VM recovery, and visual flag recovery.

The simplified target is 60–120 minutes for a competent reverser and under three
hours for an intended CTF team. If the encrypted records take more than 60
minutes to locate, add a non-magic format hint or reduce inlining around
`open_asset`. If the stream transform takes over 45 minutes after it is found,
keep `crypt_asset` as `#[inline(never)]`. Reversing LZW or reconstructing frame
disposal must not be necessary.

Reject the build if `strings` reveals the real flag or if a source GIF contains
the production flag. The documented placeholder is an intentional decoy.
Obtaining the flag by decrypting the carrier, emulating its visual program, and
viewing the resulting frame is the intended solve.

Confirm the tester never receives source, the patch, builder, solver, source
maps, symbols, or Cargo artifacts. Have the tester provide their solve script
and notes; archive those privately with the exact release SHA256.
