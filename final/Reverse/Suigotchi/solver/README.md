# Author notes: Suigotchi

Keep this file and `solve/` out of player handouts.

## Intended solve

1. Inspect the Electron package and locate the native `.node` module loaded by the main process.
2. Launch with `npm run debug` (or pass `--inspect=9229` to the packaged executable) and connect to the local V8 inspector.
3. Pass a zero suspicion value through the main-process runtime methods when local instrumentation raises the score; the author script does this directly.
4. Use the main-process runtime and native bridge to reset the pet and replay the hidden care ritual, carrying the returned signature after every transition.
5. Call the native reward check with the final state and signature.

`node solve/solve.js` automates the author path against the inspector on `127.0.0.1:9229`. The game UI does not expose hidden care IDs. The renderer receives only the three visible meters and string-based ordinary care actions; the main process rejects any other UI action name.

The ritual is Comet (6), Feed (1), Play (3), Psychoaxe (7), Shower (2), Sing (5), Play (3), Comet (6). It must pass through the native transitions so the chained `careHash` is valid. The tuned byte fields yield:

```text
hunger=39 bath=187 fun=74 mood=201 tick=8
careHash=0x3768db25e238c107
```

The native-derived initial hash is `0x3bf8f0356ee4ac51`. Sing XORs Bath by `0x95`; Psychoaxe XORs Hunger by `0x1d`, adds 41 to Fun, and XORs Mood by `0xfc`. Other transition values follow the original challenge brief.

The reward stream key depends on the complete state and history hash. Flipping the native final comparison without recreating that state produces non-flag bytes. The signature prevents simple save-file edits, but is intentionally a reversing speed bump rather than production cryptography.

## Build and packaging

Run `python3 scripts/encrypt_flag.py` after changing the reward, then `npm run dist:linux`. It writes the encrypted byte array to `native/reward_blob.h`; the literal reward is kept in author-side files only. `electron-builder` packages the app into ASAR and unpacks the native addon alongside it. Linux builds require `g++` and target the host architecture.
