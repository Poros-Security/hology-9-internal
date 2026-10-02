# Sui++

**Category:** Pwn  
**Difficulty:** Medium-Hard

This package contains the player-facing source and deployment setup. Connect to a running instance with `nc <host> <port>`.

## Run locally

Install Docker and Docker Compose. The checked-in `suipp` is the stripped challenge binary. To rebuild it from the included C++ source, install `g++`, `make`, and `binutils`, then run:

```bash
make
```

Start the service on port 1337:

```bash
docker compose up --build
```

`flag.txt` contains a local placeholder. Set `GZCTF_FLAG` before starting Compose to test with a flag value; GZCTF supplies this variable per DynamicContainer instance.

The package includes `chall.cpp`, the hardened Makefile, Dockerfile, Compose file, and `run.sh`. The solver and competition flag are not included.
