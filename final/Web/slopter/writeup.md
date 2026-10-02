# Slopter

**Category:** Web

**Difficulty:** Hard

**Flag:** `HOLOGY9{slopter_7f81874533[TEAM_HASH]07a3bf515e}`

## Overview

A coupon platform for small cafes. Flutter Web dashboard, Dart API, one container behind nginx. The source ships.

Merchants mint voucher codes inside campaigns and redeem them at the counter. Every redemption POSTs to a till URL the merchant sets.

The flag is in `GET /api/settings`, which needs a key carrying `settings:read`. The account starts with one key that lacks it.

## Solution

Two bugs, both in `src/backend/lib/`. `solver/solve.py` runs the chain.

1. `settings:read` arrives one way only. `_applyEffect` advances the partner tier by one per redemption, and tier 2 is the only path to a key that has it.

    ```dart
    merchant.tier = min(2, merchant.tier + 1);
    if (merchant.tier < 2) {
      actingKey.grant.merge(const ['campaigns:analytics']);
      return 'partner tier ${merchant.tier}, analytics unlocked';
    }
    final issued = store.issueKey(merchant, 'Partner key',
        const ['settings:read', 'campaigns:analytics']);
    ```

    One upgrade code per account, single use, so playing fair tops out at tier 1. Tier 2 means redeeming it twice.

2. `redeem` checks `voucher.used`, awaits the till notification, then commits.

    ```dart
    if (voucher.used) return _error(400, 'code already redeemed');

    final notified = await _notifyTill(store.callbackFor(voucher), voucher);
    if (!notified) return _error(502, 'till did not accept the redemption');

    voucher.used = true;
    voucher.redemptions++;
    ```

    shelf serves concurrent requests on one isolate and `await` yields it, so a second request clears the `used` check while the first is parked in `_notifyTill`.

    Not a race. The till URL is yours, set through `PATCH /api/me`, and it is read when the handler starts, so the two sends can use different listeners. Point the first at one that hangs, change the URL, send the second at one that answers instantly, release the first. Two Repeater tabs, no concurrency tooling. Both listeners must answer under 400 within the 15 second timeout or the redemption aborts without committing.

3. Both commit, the tier reaches 2, the partner key is issued. The second commit then sees `redemptions > 1` and suspends every key on the account, so the key you just earned is dead on arrival.

4. Suspension is a `Set<Grant>` holding the live grant object, and `Grant` hashes over a scope that `replaceScope` edits in place.

    ```dart
    bool isRevoked(ApiKey key) => revoked.contains(key.grant);

    void replaceScope(Iterable<String> next) {
      final sorted = next.toSet().toList()..sort();
      scope..clear()..addAll(sorted);
    }

    @override
    int get hashCode => Object.hashAll([keyId, ...scope]);
    ```

    Dart requires a key's hash code to stay fixed while it sits in a hash container, and nothing enforces it. Change the scope and the grant is still in the set but hashes to a different bucket, so `contains` misses it.

5. The partner key carries `{campaigns:analytics, settings:read}`, so a strict subset can drop one and keep the one you want.

    ```
    POST /api/keys/<partner key>/narrow   {"scope": ["settings:read"]}
    ```

    `narrow` authenticates on the session rather than the acting key, so a suspended key can still be narrowed by its owner. The grant rehashes, falls out of `revoked`, reports `active`, and `GET /api/settings` returns the flag.

## Running the solver

```
pip install -r solver/requirements.txt
python solver/solve.py http://<host>:<port>
```

The solver runs its own till listener, so the container has to reach the box running it. `--callback-host` sets the address it advertises, `--bind` the interface it listens on. It needs a fresh instance, because the upgrade code is single use.

## Difficulty mapping

Scored for the final, where no AI assistance is allowed.

| Parameter | Level | Why |
|---|---|---|
| Multifaceted skills | Hard | Web exploitation plus reading Dart cold. shelf's concurrency model and Dart's hash container contract have to come out of the language docs, and neither is something a web player carries. |
| Complex code / payload / bypass | Hard | Nothing to craft, but the delivery is unconventional. Hold one connection open, swap the till URL so the second request answers instantly, release the first. Searching for any of it returns nothing. |
| Multiple steps | Medium | Two bugs, four requests, strictly ordered. Neither reaches the flag alone. |
| Dynamic elements | Easy | Nothing changes on its own. State is in memory and resets with the container. |
| Hidden attack vectors | Insane | Mutating a key while it sits in a hash container is absent from most players' repertoire, and no CTF writeup uses it. |

Mean 3.6 of 5, which rounds to **hard** at 72%.

Two of those five lean on the no-AI rule. With a model to hand, reading unfamiliar Dart and recognising a check-then-act across an `await` both drop to routine, and the same challenge scores 3.2 and medium. It is a final-only hard.

Expect first blood near an hour and a low solve count. Step 2 is a class most web players know; step 4 is where the field splits.

## Before you change anything

The code carries no comments, so the constraints it depends on are written down here.

The till POST must sit between the `used` check and `voucher.used = true`. Move it above the check or below the commit and bug 2 disappears with nothing in the app to say so.

`Grant.hashCode` must derive from `scope`, `scope` must stay mutable, and `replaceScope` must edit the existing list rather than build a new `Grant`. `revoked` must be a `Set<Grant>` holding the live object. Switching it to a `Set<String>` of key ids is the correct design and kills bug 4.

Anti-abuse must suspend **every** key on the account, not just the offending one. Per-key suspension leaves the outcome depending on which interleaved redemption commits second, and when the tier 2 one loses that order the partner key is never suspended and bug 4 is skipped entirely.

`narrow` must authenticate on the session, not on a live acting key. Gate it on the acting key and every key is suspended by that point, so nothing can be narrowed and the challenge is unsolvable. For the same reason the tier 2 key must carry two permissions: with only `settings:read` no strict subset keeps it and narrowing always fails.

The container must reach the player's listener. Without egress the challenge cannot be solved and nothing in the app explains why. Test it on the real platform first: set `tillUrl` to a listener you control, redeem any campaign code, and look for `{"effect":"credit"}` rather than `502`.

State is in memory and the upgrade code is single use per instance, so a player who redeems it once normally can never reach tier 2 and has to respawn. Instances must stay disposable.

Keep `--pwa-strategy=none` on the Flutter build, or players keep running a cached build after a restart and see stale UI with nothing explaining why.

Rebuild `dist/slopter.zip` after any change under `src/`:

```
zip -qr dist/slopter.zip src -x 'src/backend/.dart_tool/*' 'src/frontend/.dart_tool/*' 'src/frontend/build/*'
```
