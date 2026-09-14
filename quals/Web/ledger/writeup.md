# Ledger

**Category:** Web

**Difficulty:** Hard

**Flag:** `HOLOGY9{ledger_e792d8da3b[TEAM_HASH]385b734c7a}`

## Overview

An invoice approval tool. Fastify serves both a JSON API and a built Angular SPA from one port, with nothing in front of it. No source ships. Players get an employee account.

The flag sits in an invoice's `internal_note`, which only the admin export returns, and only for staff.

## Solution

Two 2026 CVEs chained. Neither alone reaches the flag. `solver/solve.py` runs the whole thing with no dependencies.

1. Fastify's default 404 identifies the framework. Searching for a Fastify middleware bypass surfaces the `@fastify/middie` advisories.

    ```
    {"message":"Route GET:/api/nope not found","error":"Not Found","statusCode":404}
    ```

2. Grepping the initial bundle for `admin` finds only the client-side route and the chunk it lazy-loads. Fetching that chunk gives the admin prefix and the route tails as separate literals, to be reassembled by reading.

    ```js
    {path:`admin`,loadComponent:()=>import(`./chunk-CVxy8817.js`)...}
    var E = `/ops`
    this.http.get(`${E}/export`, { params: { includeInternal: ... } })
    ```

3. CVE-2026-85184. `@fastify/middie` 9.1.0 through 9.3.3 matches path-scoped middleware against the raw request target, while `find-my-way` resolves an absolute-form target to its path before dispatching. The guard on `/ops` never runs, the handler does, and the authority is not validated.

    ```
    GET http://anything/ops/export HTTP/1.1
    Host: whatever
    ```

    No browser can send this. It needs `curl --request-target`, a raw socket, or Burp. The sibling CVEs are already patched: `//ops/export` gives 404 and `/%6fps/export` gives 401.

4. The bypass alone returns nothing useful. Rows come back without `internal_note`, the other admin routes repeat the role check inside their handlers, and `?includeInternal=true` is ignored because the handler builds its options object from the session and never merges request input into it.

5. CVE-2026-33863. `/ops/settings/import` applies an uploaded file with convict's `loadFile()`, and convict 6.2.4 merges it through an `overlay()` that does not filter dangerous keys.

    ```json
    {"__proto__":{"includeInternal":true}}
    ```

    Posting that as a JSON body fails. Fastify parses JSON with `secure-json-parse`, which rejects `__proto__` and `constructor.prototype` and answers `400 FST_ERR_CTP_INVALID_JSON_BODY`. The file route works because multipart bytes go to disk and are read back by convict, never passing through the body parser.

6. Request the export through the bypass again. `opts.includeInternal` now resolves through the polluted prototype and the rows carry `internal_note`.

## Running the solver

```
python solver/solve.py http://<host>:<port>
```

The solver uses the standard library only. Neither `requests` nor ordinary `curl` usage can send an absolute-form request target, so it speaks HTTP through `http.client`.

## Difficulty mapping

Scored against [dimasma0305's calculator](https://dimasma0305.github.io/ctf-challenge-difficulty-calculator/), which averages the five parameters.

| Parameter | Level | Why |
|---|---|---|
| Multifaceted skills | Hard | One domain worked at depth, spanning bundle recon, turning advisory prose into a working request, prototype pollution, and hand-writing HTTP because no ordinary client sends an absolute-form target. |
| Complex code / payload / bypass | Hard | The payloads are short but neither can be delivered normally. One needs a hand-written request line, the other needs multipart because the JSON parser blocks it. |
| Multiple steps | Hard | Six stages, and the middle one is a visible dead end that has to be recognised as such. |
| Dynamic elements | Easy | Nothing changes on its own. The pollution is permanent but the player causes it. |
| Hidden attack vectors | Hard | Absolute-form request targets are absent from most players' repertoire, and delivering pollution through a config-file import rather than a JSON body is off the usual path. |

Mean 3.6 of 5, which rounds to **hard** at 72%.

## Before you change anything

The code carries no comments, so the constraints it depends on are written down here.

Nothing may sit in front of Fastify. nginx parses an absolute-form target and forwards origin-form upstream, which kills stage 3 with no error anywhere. Measured both ways, the bypass works direct to Fastify and fails behind nginx 1.27. `ng build` must stay on the browser builder for the same reason, since Angular's SSR would put a Node server in the path. GZCTF must run `PortMappingType: Default`.

The export handler must **omit** `includeInternal` for non-staff rather than set it to `false`. An own property shadows the prototype, so `{ includeInternal: false }` defeats the pollution entirely. Write `role === 'staff' ? { includeInternal: true } : {}`.

Three checks pull against each other and decide whether the challenge works. The built bundle must contain `includeInternal` and the route tails as literals, which makes stage 5 solvable. `?includeInternal=true` must still return redacted rows before pollution, which keeps stage 5 necessary. And an unknown path under `/api` or `/ops` must return Fastify's default 404 body, which is what makes stage 1 possible. Run all three after touching the export handler, the API calls or the not-found handler.

Never build a path from anything that is not itself a literal in the source. `'/op' + 's/export'` is pointless, since esbuild folds plain concatenation back into one string. A template literal against a module const stays split, which is what the admin chunk uses.

Both package pins are load-bearing. `@fastify/middie` 9.3.4 patches the bypass and `convict` 6.2.5 patches the pollution. The lockfiles are committed. The UI build stage needs Node 24 and npm 11, because Angular 22 fails to install on npm 10.

Prototype pollution is process-global and survives until restart, so one solver unredacts the export for everyone sharing that instance. The challenge needs per-team instances.

## Rechecking before the event

Neither CVE had a public proof of concept as of September 2026, though the advisory for CVE-2026-85184 describes the absolute-form technique in prose and gives an example request. The sibling middie CVEs all have public exploitation detail. Recheck both immediately before the event, because a published exploit turns stage 3 from reading into copying.
