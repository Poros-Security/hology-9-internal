# SuiJail

A five-cell misc challenge where the terminal map is the application state. The only player interface is an expression-only Python prompt: move through ordinary game methods, inspect the objects that govern the prison, and exploit one different capability mistake in each cell. Gates, guards, cameras, and the final completion ledger are live Python objects used by both the evaluator and renderer.

## Play Locally

Requirements: Python 3.11 or newer. The game uses only the standard library.

```sh
cd src
python3 main.py
```

The local flag defaults to `FLAG{development_flag}`. Set a local value before starting:

```sh
cd src && FLAG='FLAG{local_test}' python3 main.py
```

## Docker

```sh
cd src
docker compose build
docker compose up
```

Then connect with:

```sh
nc localhost 31337
```

For a custom local flag:

```sh
cd src && GZCTF_FLAG='FLAG{local_test}' docker compose up --build
```

There is no downloadable attachment, so this challenge intentionally has no `dist/` directory.

The short-lived container launcher uses only `SETUID` and `SETGID`; the game server runs as UID 10001 and the reward daemon as UID 10002. Compose applies a 256 MiB memory limit, drops other Linux capabilities, and uses a read-only root filesystem with a small `/tmp` for the private reward socket. `AUTHOR_NOTES.md`, solvers, and tests are excluded from the image. The image intentionally omits Docker's `EXPOSE` instruction because GZCTF maps the port declared by challenge metadata.

## GZCTF DynamicContainer

`challenge.yml` uses the event's DynamicContainer template. The build script creates the image from `src/Dockerfile`; GZCTF exposes container TCP port `31337`. Set the event's desired flag prefix in `container.flagTemplate`; the sample uses `FLAG{[TEAM_HASH]_[GUID]}`. GZCTF supplies each running team container's value through `GZCTF_FLAG`.

The server removes `GZCTF_FLAG` from its environment at startup and gives the value only to the separate reward daemon. The game can request a flag only after the daemon has accepted the ordered receipt for all five stages. There is no static production flag in the repository or the game module globals.

Resource defaults in `challenge.yml` are 256 MiB, one GZCTF CPU unit, and 256 MiB storage. Tune those with the event's expected connection count and lifetime.

## Interface

Each connection starts at Jail 1 unless a valid checkpoint is entered. The console accepts Python expressions only and exposes one game object, `player`, plus a small set of real Python built-ins (`dir`, `getattr`, `repr`, `type`, `len`, and collection helpers). There are no custom `look`, `inspect`, `move`, or `help` shell functions. Discover the live object graph with `dir(player)` and read values with expressions such as `repr(player.position)` or `getattr(player, "position")`. In the early cells, `getattr` is subject to the same per-cell attribute allowlist as dotted access. The avatar itself accepts cardinal directions as calls, for example `player("south")`.

The screen redraws after each expression. ANSI colors are enabled when the terminal supports them. Set `NO_COLOR=1` or `TERM=dumb` to disable color; set `FORCE_COLOR=1` for a raw netcat deployment that should always receive color codes. `:quit` closes a session without invalidating its latest checkpoint.

| Cell | Intended concept | Live state change |
| --- | --- | --- |
| A | Mutable object despite eval-only syntax | Use `getattr` and the list's native mutator to change coordinates |
| B | Indirect object graph traversal | Discover the guard with `dir` and clear its policy tags |
| C | Bound method capability leak | Follow `player.warden.__self__` to the remote actuator |
| D | Hardened AST with an exposed callback | Call the avatar's captured maintenance capability |
| E | Game abstraction manipulation | Reach the manager through the Warden owner and complete its ledger |

The shell presents useful runtime exceptions and distinct syntax-policy, size-limit, and timeout errors. AST policies differ by cell and constrain node types as well as attribute names, including literal attribute names passed to the genuine `getattr` built-in. Jail 4 rejects attribute and subscript syntax; its callable avatar is the application capability that survives that restriction. The evaluator has a 240-character expression cap, 80-node syntax cap, 350 ms evaluation deadline, 1200-character output cap, and recursion limit. Connections have a 300-second idle timeout, 512-character line limit, 700-expression limit, and burst limit.

## Checkpoints

After each cell, the game prints a signed token such as `PYJAIL-3-<session>-<mac>`. Enter the latest token at the reconnect prompt to resume at the next cell; a completed fifth-cell token can reclaim the flag from the same live container. The token authenticates both the completed stage and reward-daemon session, so plaintext level edits do not restore progress. Tokens live for the lifetime of the challenge container; a container restart starts a fresh reward ledger and invalidates outstanding tokens.

## Tests And Solvers

Run the automated unit and service tests with:

```sh
cd src
pytest -q
```

Start the server in one terminal and solve it from another:

```sh
cd src
python3 server.py
```

In another terminal, from the challenge root:

```sh
python3 solver/solve_all.py 127.0.0.1 31337
```

Each `solve_jailN.py` uses the intended payloads through Jail N. For stages after the first, it can continue a prior connection by passing `--checkpoint TOKEN`. The full solver connects once, completes all five stages, and prints the flag returned by the reward service.

## Layout

```text
src/engine/   game model, renderer, console, world and entities
src/levels/   five independent stage definitions
src/security/ AST allowlists, per-level policies and timed evaluator
src/reward/   UNIX-socket flag service and authenticated client
src/tests/    movement, exploit, policy, checkpoint, timeout and isolation tests
src/server.py process-per-connection TCP service
src/main.py   local stdio mode
src/runtime.py flag handoff and reward daemon lifecycle
solver/       official network solvers
challenge.yml GZCTF DynamicContainer metadata
```

The challenge is intentionally vulnerable at the application layer; the evaluator is a game puzzle, not a general-purpose security boundary. Run it inside the supplied constrained container or an equivalent isolated challenge runtime.
