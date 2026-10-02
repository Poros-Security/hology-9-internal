# Hology7 Incident

Category: Misc

Topic: Absurd Chess Rule Engine / Deterministic Game Bot

Difficulty: Medium-Hard Finals, about 7/10

Description:

FIDE was busy.

## Rules

- White is controlled by the player.
- Black is controlled by a deterministic fake Magnus Carlsen.
- Knights move like normal FIDE knights.
- Kings move one square like normal kings.
- Every other piece moves like a queen.
- Kings cannot be captured.

## Gauntlet

- Beat Magnus 7 times in a row to get the flag.
- Rounds 1-4 are mate in 3 and rounds 5-7 are mate in 4. Every board has a 5 move budget, so mate in 3 boards leave 2 spare moves and mate in 4 boards leave 1. This keeps each board solvable by hand inside the clock.
- Boards are crowded on purpose: white has 3 to 5 attacking pieces besides the king (doubled knights, rooks and so on), black has 1 to 4 defenders.
- Each board has a 2 minute clock. The clock starts when the board is dealt and pauses between rounds.
- Running out of moves or time ends the run and resets the streak. Press New to start over (3 second cooldown).
- Refreshing the page resumes the current run. After a loss it starts a new run; after a win it keeps showing the flag.
- Boards are dealt from a shuffled per-session deck over the bank in `src/puzzles.json`.

Magnus trash talks in the chat panel after every move. The lines are cosmetic only; his moves stay deterministic.

## Flag

The flag is dynamic per team. GZCTF injects it as `GZCTF_FLAG` from the template in `challenge.yml`:

```
HOLOGY9{0nly_th3_0G_kN0wS_Wh4t_h44p3n3d_1n_H0loGy7_[TEAM_HASH]}
```

The server reads `GZCTF_FLAG`, then `FLAG`, then falls back to `HOLOGY9{redacted}`.

## API

- `GET /api/state` current run; `?fresh=1` starts a new run only if the last one was lost.
- `GET /api/new` start a new run (3 second cooldown).
- `POST /api/move` with `{"move": "a1b2"}`.
- `POST /api/next` deal the next board after a round is cleared.

## Run

```bash
cd src
GZCTF_FLAG='HOLOGY9{0nly_th3_0G_kN0wS_Wh4t_h44p3n3d_1n_H0loGy7_local}' python3 server.py
```

Open `http://127.0.0.1:8085`. `ROUND_SECONDS` overrides the 120 second clock for testing.

## Solve

```bash
python3 solver/solve.py http://127.0.0.1:8085
```

The reference solver is a breadth-first search over white moves with Magnus's replies simulated. On the reference machine it needs 0.2 to 34 seconds per board (median about 2s for mate in 3 and 7s for mate in 4), well inside the 2 minute clock. The bank holds 110 boards (60 mate in 3, 50 mate in 4). Every board was proven with the reference solver to be a forced mate at exactly its listed depth, with no shorter mate, and boards were filtered so that only a few first moves keep the shortest forced win.
