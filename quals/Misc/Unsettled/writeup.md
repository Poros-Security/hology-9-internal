---
title: "Unsettled"
ctf: "HOLOGY9"
date: 2026-09-11
category: web
difficulty: medium
points: 1000
flag_format: "HOLOGY9{...}"
author: "Ariq Ardian"
---

# Unsettled

## Summary

`BatchMarket.multicall()` restores a rebate from a snapshot taken before the
batch. A reward-token callback can claim the newly accrued rebate during the
purchase, after which `multicall()` restores another claimable rebate from the
stale snapshot. This refunds all spent credit while retaining the reward.

## Solution

### 1. Duplicate each batch rebate

For a 10,000-credit purchase, `purchase()` accrues a 5,000-credit rebate and
then transfers reward tokens to the exploit contract. Its
`onRewardReceived()` callback immediately calls `market.claim()`, collecting
the first 5,000 credits and zeroing the live claimable value.

When execution returns to `multicall()`, it calls `sync()` with the stale
pre-batch snapshot plus the batch rebate. A normal `claim()` after the batch
collects a second 5,000 credits. The exploit can therefore spend the same
10,000 credits ten times and retain 100,000 reward tokens.

The complete executable solver is [`solver/solveme.py`](solver/solveme.py).
It compiles and deploys the callback contract, grants it the player's initial
credit allowance, executes ten vulnerable batches, and checks `isSolved()`.

### 2. Reproduce locally

The validation used Foundry 1.4.4, Web3.py 7.13.0, and a local Solidity 0.8.30
compiler targeting the Shanghai EVM. On a fresh Anvil chain, run:

```bash
# Terminal 1
anvil --host 127.0.0.1 --port 8545 --hardfork shanghai
```

```bash
# Terminal 2, from Batch Market/src
export SOLC=/home/acunetix/.local/share/svm/0.8.30/solc-0.8.30
FOUNDRY_SOLC="$SOLC" FOUNDRY_OFFLINE=true forge create \
  contracts/Setup.sol:Setup \
  --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80 \
  --rpc-url http://127.0.0.1:8545 \
  --broadcast \
  --constructor-args 0x70997970C51812dc3A010C7d01b50e0d17dc79C8

cd ../solver
export RPC_URL=http://127.0.0.1:8545
export PRIVATE_KEY=0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d
export SETUP=0x5FbDB2315678afecb367f032d93F642f64180aa3
python3 solveme.py
```

The addresses and keys above are Foundry's public default test accounts and
are only appropriate for a local Anvil chain. The verified output was:

```text
Exploit : 0x8464135c8F25Da09e49BC8782676a84730C318bC
Solved  : True
```

An independent state query returned a player reward balance of
`100000000000000000000000` wei (100,000 tokens) and `isSolved() == true`.

## Flag

The contract-only local deployment proves the solved condition but does not
run the launcher that returns the per-team flag. The configured dynamic flag
format is `HOLOGY9{...}`.
