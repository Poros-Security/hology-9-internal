# Suigotchi

Suigotchi is a cozy desktop pet game built with Electron. Feed, shower, play with, and tuck in a tiny star fumo while keeping an eye on Hunger, Bath, and Fun. A native Node-API module owns the hidden pet state and reward check.

## Build on Linux

Requirements: Node.js 22 or newer, npm, a C++17 compiler (`g++`), and standard Linux desktop libraries.

```sh
npm install
npm start
```

Build a Linux AppImage, a no-FUSE tarball, and an unpacked runnable directory:

```sh
npm run dist:linux
```

If your machine has FUSE 2 available, launch the AppImage:

```sh
./dist/Suigotchi-1.0.0-x86_64.AppImage
```

If it reports a missing `libfuse.so.2`, use the bundled tarball instead:

```sh
tar -xzf dist/Suigotchi-1.0.0-x64.tar.gz
./Suigotchi-1.0.0-x64/suigotchi
```

You can also ask the AppImage to extract itself for that launch with `./dist/Suigotchi-1.0.0-x86_64.AppImage --appimage-extract-and-run`; this extracts a temporary copy each time. The AppImage, tarball, and unpacked app are written to `dist/`. The executable in the unpacked build is `dist/linux-unpacked/suigotchi`. Build output is for the Linux architecture used to build it. `npm run debug` starts the app with the local V8 inspector enabled for challenge authoring.

Pet saves live in Electron's per-user application data directory. The game has no network service and uses no device-specific secrets. The `solve/` folder and reward generator are author materials and are excluded from the packaged app.

## Challenge

Suisei's visible care meters tell only part of the story. The challenge is to understand the runtime bridge between the Electron main process and the stripped native addon, then discover what kind of care the little comet remembers. Wrong sky checks give gentle hints. Normal game buttons only perform ordinary care actions.

## Project map

- `electron/`: secure main/preload bridge and the pet-care interface
- `native/`: native state machine and encrypted reward bytes
- `scripts/build-native.cjs`: Linux Node-API addon build
- `scripts/encrypt_flag.py`: author-side reward blob generator
- `solve/solve.js`: reference V8-inspector solve script
- `dist/`: generated Linux game packages
