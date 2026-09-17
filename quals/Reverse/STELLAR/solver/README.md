# STELLAR organizer solver

Run from any directory:

```bash
./solver/run.sh
```

The wrapper extracts the AppImage, runs the independent Rust solver against the
inner stripped ELF, and writes `solver/revealed.ppm`. Open that image to read the
flag. 
