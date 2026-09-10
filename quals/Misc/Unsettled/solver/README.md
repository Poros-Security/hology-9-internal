# Batch Market Solver

Install Python dependencies and ensure `forge` is available, then export the
instance values displayed by the launcher:

```sh
python -m pip install -r requirements.txt
export RPC_URL='https://challenge.example/<instance-uuid>'
export PRIVKEY='<player-private-key>'
export SETUP_CONTRACT_ADDR='<setup-address>'
python solve.py
```

The solver deploys `solution/Attacker.sol`, transfers the player's initial
credit to it, and re-enters the rebate claim during each reward callback. The
stale batch snapshot restores already-claimed rebates, allowing the next batch
to grow until the player owns enough reward tokens to satisfy `isSolved()`.
