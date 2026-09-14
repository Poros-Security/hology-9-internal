# Mekanik Tua

**Category:** Web

**Difficulty:** Hard

**Flag:** `HOLOGY9{mekanik_tua_667d023b29[TEAM_HASH]18f5493820}`

## Overview

A job tracker for a motorcycle workshop. A Node frontend owns the browser session and proxies three actions to a PHP API that is not reachable from outside. The source ships with the challenge.

The flag sits in `owner_notes`, readable only through the API's `admin` action, which the frontend never proxies.

## Solution

Six stages. Each one's output is the next one's input. `solver/solve.py` runs all of them.

1. The frontend checks `req.query.action` against an allowlist, then forwards `req.url` raw. Node keeps `action` and `action\0` as two separate keys. PHP cuts parameter names at the null byte and the later value wins, so the allowlist sees `list` while the API runs `config`.

    ```
    /api?action=list&action%00=config
    ```

2. The `config` action refuses credential fields with `preg_match('/pepper|secret|key/iu', $fields)`. The `u` modifier makes PCRE validate the subject before matching, so malformed UTF-8 returns `false` instead of `0` and the guard never fires. `explode` splits the bad fragment away from the field name.

    ```
    /api?action=list&action%00=config&fields=app_pepper,%C3%28
    ```

3. `action%00=users` returns every username, `password_hash`, `pw_salt` and `role`, including the staff account `pakwid`.

4. Lockout is enforced at the API, so online guessing is dead. Hashes are `bcrypt(pepper . password . salt)` at cost 10. bcrypt reads only the first 72 bytes and the pepper is 64 characters, so exactly 8 password bytes survive and the salt sits entirely past the cut. The staff password starts `adm-` and continues in hex, leaving four hex characters to search, 65,536 candidates.

    The salt is a decoy, and cracking with the wrong salt or none at all works just as well. The search takes around four minutes on 16 cores.

5. `action%00=login&u=pakwid&p=<cracked prefix>` returns the API session id. Those eight characters authenticate on their own.

6. The frontend drops any incoming cookie named `api_sid` and appends its own last. Send it under a name that filter misses. PHP rewrites the dot to an underscore and keeps the first of the two, which is the injected one.

    ```
    Cookie: api.sid=<staff session id>
    /api?action=list&action%00=admin
    ```

## Running the solver

```
pip install -r solver/requirements.txt
python solver/solve.py http://<host>:<port>
```

It discovers the pepper, the staff account and the password on its own, so it survives a reseed or a pepper rotation.

## Difficulty mapping

Scored against [dimasma0305's calculator](https://dimasma0305.github.io/ctf-challenge-difficulty-calculator/), which averages the five parameters.

| Parameter | Level | Why |
|---|---|---|
| Multifaceted skills | Hard | Web exploitation plus source review, plus writing a parallel offline cracker and reasoning about bcrypt's input handling. |
| Complex code / payload / bypass | Medium | The payloads are short and the source ships, but `%C3%28` only works if you know what a malformed UTF-8 lead byte does to PCRE. |
| Multiple steps | Hard | Six stages, strictly ordered, and no stage confirms the previous one was right. |
| Dynamic elements | Medium | Pepper, session secret and staff password are generated per instance, so nothing can be precomputed and a restart invalidates a cracked password. |
| Hidden attack vectors | Hard | Null-byte parameter truncation across two parsers, PCRE returning `false` rather than `0`, and PHP rewriting a dot in a cookie name then keeping the first duplicate. |

Mean 3.6 of 5, which rounds to **hard** at 72%.

## Before you change anything

The code carries no comments, so the constraints it depends on are written down here.

The pepper is 64 characters and the staff password is `adm-` plus hex. Together those put the bcrypt cut at exactly four crackable hex characters. Move either and the challenge turns unsolvable or falls open, with nothing in the app to say which.

Stage 6 works because the frontend appends its own cookie last. Reorder that and the attack stops, and the response looks exactly like an exploit that was simply wrong.

The pepper, session secret and staff password are generated at container start and the database is rebuilt with them, so the instance has to stay disposable. Persist the database across restarts and every account stops working, because the hashes no longer match the new pepper.

Every seeded password is 8 characters or longer, which keeps the salt entirely outside bcrypt's window for every account. A shorter one would pull salt bytes back inside for that account alone and the decoy would behave inconsistently. `AuthController::MIN_PASSWORD` holds the same floor for accounts players create.

Rebuild `dist/mekanik-tua.zip` after any change under `src/`:

```
zip -qr dist/mekanik-tua.zip src -x 'src/frontend/node_modules/*' 'src/backend/vendor/*'
```
