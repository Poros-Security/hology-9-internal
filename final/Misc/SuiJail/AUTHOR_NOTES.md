# Author Notes - SuiJail

This file is for challenge operators and is not copied into the production image.

## Intended Discovery And Solves

The evaluator injects only the `player` object as an application name. There are no custom shell functions such as `look`, `inspect`, `move`, or `help`; exploration uses genuine Python built-ins (`dir`, `getattr`, `repr`, `type`, `len`, and basic collection helpers). `getattr` requires a literal attribute string and the policy validates that string against the active cell's allowlist, just like dotted access. `vars`, `setattr`, imports, and code-execution built-ins are intentionally absent. The player's call protocol (`player("south")`) is a game-object capability for ordinary movement, not a shell helper function.

### Jail 1: Mutable Prisoner

The evaluator parses one `eval` expression, so assignment statements fail with a real syntax error. `dir(player)` reveals `position`; `getattr` reaches that normal mutable two-item list and its native list mutator. The player begins at `[3, 2]`; the locked door is at `(4, 4)` and the corridor is at `(4, 5)`. The app checks that same coordinate list after every expression and records completion when the actor reaches the corridor.

```python
dir(player)
getattr(getattr(player, "position"), "__setitem__")(0, 4)
getattr(getattr(player, "position"), "__setitem__")(1, 5)
```

The renderer reads that same list, so the `@` moves and the stage advances. This teaches mutation without statements and without a string blacklist.

### Jail 2: The Guard

The guard is intentionally absent from the shell locals. `dir(player.room.entities[1])` lets the player examine the anonymous room entity; entity index 0 is a terminal, index 1 is Officer K, and index 2 is another terminal. The guard's movement policy is the mutable set `protocol`; the map and collision checker both read its `blocking` tag.

```python
dir(player.room.entities[1])
getattr(getattr(getattr(getattr(player, "room"), "entities")[1], "protocol"), "clear")()
player("south")
player("south")
player("south")
```

After clearing the policy set, the red `G` becomes a dim `g`; the cell gate is already open. Movement uses ordinary game rules to reach the exit.

### Jail 3: Bound To The Warden

`dir(player)` now reveals a bound `warden` method. Its `__self__` is a stage-local Warden interface that owns the world but not the game manager. `world.rooms[0]` is the current room and `world.rooms[1]` is WARDEN CONTROL. The remote actuator and the current room's gate are the same `Door` instance, so unlocking through the remote graph changes the visible `D` to `/` and permits normal movement.

```python
dir(player.warden)
getattr(getattr(getattr(getattr(getattr(getattr(player, "warden"), "__self__"), "world"), "rooms")[1], "doors")[0], "unlock")()
player("south")
player("south")
player("south")
```

This is a deliberate bound-method capability leak. The evaluator disallows unrelated dunder attributes such as `__globals__`, `__class__`, and `__subclasses__`.

### Jail 4: Hardened Interpreter

This stage's AST policy removes `Attribute`, `Subscript`, `Lambda`, comprehensions, and binary operations. `dir(player)` shows that the avatar is callable, while `repr(player)` reveals the accepted `camera_grid` channel. The callable avatar delegates to a control-button object wrapping a callback closure that captures `SurveillanceController`, which in turn owns the camera list and gate.

```python
dir(player)
repr(player)
player("camera_grid")
player("south")
player("south")
player("south")
```

The call does not traverse an object path in player syntax. It exercises an application capability already packaged in the exposed callable. The blue cameras change from `C` to `c`, the alarm controller shuts down, and the gate opens.

### Jail 5: Panopticon

There is no exit tile or gate. The bound `warden` method's owner gains a `manager` reference only in this final cell. Its completion list begins `[True, True, True, True, False]`. The manager's real `check_completion()` method validates its list, submits the fifth signed receipt, and asks the isolated reward service to release the flag.

```python
dir(player.warden.__self__)
getattr(getattr(getattr(getattr(getattr(player, "warden"), "__self__"), "manager"), "completed"), "__setitem__")(4, True)
getattr(getattr(getattr(getattr(player, "warden"), "__self__"), "manager"), "check_completion")()
```

The game abstraction is the last room. The returned flag is the reward service's response, not a field set in a level or evaluator namespace.

## Progress And Reward Boundary

The game process creates a random HMAC key and passes it to the reward daemon through its child environment. The daemon receives the dynamic flag and key; `runtime.py` removes `GZCTF_FLAG` and `FLAG` from the long-running game process environment before accepting players. In the container, the reward daemon runs as UID 10002 while the game server runs as UID 10001; only their shared challenge group can connect to the mode-0660 UNIX socket. Local stdio mode runs both processes as the current user with a mode-0600 socket. Each game has a random 64-bit session ID. Stage receipts are MAC-authenticated and the daemon accepts only the next stage number. Claims require the daemon's `{1,2,3,4,5}` ledger.

Checkpoint tokens MAC the completed stage together with the reward session ID. The reward daemon owns the receipt ledger, so reconnects to the same container can resume. The container is a per-team GZCTF DynamicContainer; restarting it resets the ledger and its process-local checkpoint key.

This is reasonable flag separation for a challenge service, not protection against root in the container, arbitrary native code execution, or a full escape from the container's OS boundary. Do not mount host secrets or the Docker socket. Keep the challenge container network-isolated if the event does not need egress.

## Possible Unintended Paths

- Earlier Python method introspection can sometimes find routes to a game's globals. Per-level AST policies deny the known universal routes (`__globals__`, `__class__`, `__dict__`, and subclass traversal) through both dotted access and literal-name `getattr` calls; the intended world graph remains available only where needed.
- `dir` is deliberately available, but names it reveals are not automatically accessible. Keep the `Policy.attributes` sets narrow when adding fields or helper methods.
- A Python `eval` sandbox is not a security boundary. An unknown evaluator escape could still read server process memory or abuse exposed capabilities. The dynamic flag is isolated in the reward process, but an attacker who gains arbitrary native execution in the container can attack sibling processes or the OS boundary.
- The reward daemon trusts authenticated stage receipts from the game process. Its socket is mode `0600`; the MAC key is generated per container boot and is not passed through eval locals. Do not change the daemon to accept unauthenticated `claim` requests.
- Any added `repr` implementation should remain small and side-effect free. The built-in `repr` is the player's value-inspection tool.
- Keep the production image copy list explicit so `AUTHOR_NOTES.md`, tests, and official solver payloads stay outside the running container.

## Difficulty Tuning

- Easier: make the room graffiti mention `__setitem__`, place a harmless entity before the guard, or show the remote room index in terminal text.
- Harder: add decoy objects to the room entity list, move the Jail 3 actuator to another room index, or make the Jail 4 callback accept a clue-derived token. Keep inspection available so the chain remains fair.
- Do not harden the challenge by stacking keyword deny lists. Change the AST node and attribute policies per stage, then re-run all five official solvers.
- For a shorter event, issue stages 1-3 as a short track and reserve 4-5 for a higher point tier; avoid weakening the fifth-stage reward ledger.

## Hint Escalation

1. Jail 1: "The bars are checked against a coordinate pair. Can the pair change without assignment?"
2. Jail 2: "Use `dir` on the room's entities; the guard does not need a local variable name."
3. Jail 3: "A bound method carries its owner. Follow that reference to the other room."
4. Jail 4: "No attribute syntax is needed to invoke a callable. Read its representation for the accepted argument."
5. Jail 5: "The manager trusts its completion ledger and has a method that releases the reward."

## Operational Checks

- Local stdio: `cd src && python3 main.py`
- TCP: `cd src && python3 server.py`, then `nc localhost 31337`
- Compose: `cd src && docker compose build && docker compose up`
- Automated suite: `cd src && pytest -q`
- Full intended solve: `python3 solver/solve_all.py 127.0.0.1 31337`

The GZCTF image should use the fork's `DynamicContainer` type and expose TCP port 31337. Set `flagTemplate` to the competition's accepted prefix. Confirm the event importer sees `container.exposePort`, `memoryLimit`, and `cpuCount` before opening the challenge.
