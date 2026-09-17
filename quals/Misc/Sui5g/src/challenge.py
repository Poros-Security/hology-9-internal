#!/usr/bin/env python3

import argparse
import json
import os
from pathlib import Path
import shlex
import signal
import sys

from policy import Denied, FREE, Network, PREMIUM, SLICES, SUPI

MAX_LINE = 2048
MAX_COMMANDS = 300
SESSION_SECONDS = 900
HELP = """Commands
  map                            Network and current location
  sim                            Read your subscription
  slices                         Broadcast slice directory
  register                       Authenticate your Free SIM
  authorize <sst> <sd> <dnn>      Request slice authorization
  session <dnn>                  Establish a PDU session
  surf <portal|vault>            Request a data service
  ticket export                  Export diagnostic handover context
  ticket import <token>          Import a signed broker capability
  plan create <sst> <sd> <dnn>   Stage a handover target
  plan show <id>                 Inspect a staged plan
  plan check <id>                Request a policy approval receipt
  plan edit <id> <sst> <sd> <dnn> Update a staged target
  plan commit <receipt>          Submit approved work to SMF
  trace                          Recent control-plane decisions
  status                         Current authorization and route
  evidence                       Machine-readable progress
  manual                         Field definitions and protocol notes
  color <on|off>                  ANSI color preference
  reset                          Restart this connection's challenge
  help                           Command reference
  quit                           Disconnect"""

MANUAL = """SuiTel NR-UE maintenance terminal / 5G basics

This console controls the NR UE session. The UE is the phone, modem or router.
Its SIM/USIM proves the subscriber identity; it does not itself grant every
service in the network. Here SIM 0042 is a Free subscriber.

The path shown by map is:
  UE       the phone/modem using the SIM
  gNB      the 5G radio base station (the tower)
  AMF      registration and mobility control
  UDM      subscriber data, including subscribed slices
  NSSF     slice selection and Allowed NSSAI decisions
  SMF      PDU-session control and route selection
  UPF      user-plane forwarding toward a data service

The UE first registers. It then asks for a PDU session. A PDU session opens a
data connection through a UPF. "session internet" means use the DNN called
internet. A DNN is the data network name, similar to an operator APN in 4G.

An S-NSSAI identifies a slice:
  SST  Slice/Service Type, written here as a decimal number.
  SD   Slice Differentiator, six hexadecimal digits.
The pair is important. Free is 1-000001. Premium is 1-000099. They share SST
1 and DNN internet but are different slices. A Requested NSSAI is what the UE
asks for; a Subscribed S-NSSAI is what UDM says the account includes; an
Allowed NSSAI is what the network actually grants. Asking for Premium does not
change a Free subscription.

Normal example:
  register
  authorize 1 000001 internet
  session internet
  surf portal

The broker is an authenticated maintenance path. Diagnostics and mobility work
is normally performed by OAM/management systems and protected service-to-service
interfaces. A short-lived signed context or capability can authorize a
troubleshooting operation, carry a trace reference, or bind a mobility
transaction to a subscriber/session.

The maintenance ticket is a one-use, connection-bound handover context encoded
as URL-safe base64(payload).hex-signature. Handover scope allows a plan to be
staged. Plans have an ID, target and revision. Policy returns a signed receipt
for an allowed target, and SMF consumes that receipt before a new session is
installed.

Use trace to read control-plane events, status to read current state, map to
see the route, and evidence to see the machine-readable result. Each TCP
connection has an independent subscriber context, keys and plans.
"""


def slice_args(args):
    sst, sd, dnn = args
    if not sst.isascii() or not sst.isdecimal() or not 1 <= int(sst) <= 255:
        raise ValueError("SST must be an integer from 1 to 255.")
    if len(sd) != 6 or any(c not in "0123456789abcdefABCDEF" for c in sd):
        raise ValueError("SD must contain exactly six hexadecimal digits.")
    return int(sst), sd.lower(), dnn


class Console:
    def __init__(self, flag, *, secure=False, output=None):
        self.network = Network(secure=secure)
        self.flag = flag
        self.output = output or sys.stdout
        self.color = True

    def paint(self, text, color):
        return f"\033[{color}m{text}\033[0m" if self.color else text

    def say(self, text="", color=None):
        print(self.paint(text, color) if color else text, file=self.output, flush=True)

    def graph(self):
        n = self.network
        self.say("\n  SuiTel NR-UE maintenance console", "1;36")
        self.say("  " + "=" * 62)
        ue_state = "ATTACHED" if n.registered else "SEARCHING"
        ue_color = "32" if n.registered else "36"
        self.say("       .----------.                         /\\", ue_color)
        self.say("      /  ________  \\                       /||\\")
        self.say("     |  | SIM    |  |                     / || \\")
        self.say(f"     |  | FREE   |  |                    /__||__\\")
        self.say(f"     |  |________|  |                       ||")
        self.say(f"     |    nr-ue   |  {ue_state:<8}              ||")
        self.say("      '----------'                          ||")
        self.say("       PHONE / SIM                            ||")
        self.say("                                             ||")
        self.say("        UE device  -------- N1 / RLS -------- 5G TOWER")
        ue = "[ UE / FREE SIM / YOU ]" if not n.registered else "[ UE / FREE SIM ]"
        self.say(f"  {ue:<28}--N1--> [ gNB ]", "36")
        self.say("                                         | N2")
        amf = "[ AMF / YOU ]" if n.registered and n.active is None else "[    AMF    ]"
        self.say("                                   " + amf, "36")
        self.say("                                         |")
        self.say("                     [ UDM: FREE ] <-- [ NSSF ]", "33")
        self.say("                                         | Allowed NSSAI")
        self.say("                                      [ SMF ]")
        self.say("                                         ^")
        self.say("                [ Broker ] --> [ Policy queue ]", "33")
        self.say("                                         |")
        self.say("                  +----------------------+---------------+")
        self.say("                  |                                      |")
        self.say("            [ Free UPF ]                           [ Premium UPF ]")
        self.say("              1-000001                               1-000099")
        self.say("                  |                                      |")
        free = "[ portal / YOU ]" if n.active == FREE else "[ portal ]"
        premium = "[ vault / YOU ]" if n.active == PREMIUM else "[ vault / LOCKED ]"
        self.say("      " + self.paint(f"{free:^24}", "32" if n.active == FREE else "37")
                 + "               "
                 + self.paint(f"{premium:^24}", "32" if n.active == PREMIUM else "31"))
        route = f"UE > gNB > {n.active.name} UPF" if n.active else "No data route"
        self.say(f"  Route: {route}", "1;32" if n.active else "33")
        self.say(f"  Broker: {'handover' if n.handover else 'inspect'} | Plans: {len(n.plans)}", "36")
        self.say("  Subscription: FREE | Model: SuiTel training core\n", "90")

    def banner(self):
        self.say("\n  S U I T E L  N R - U E", "1;36")
        self.say("  Network access and mobility console", "1;37")
        self.say("  SIM 0042 / Free subscription / Vault requires Premium")
        self.graph()
        self.say("  help | sim | slices | register | trace", "36")

    def execute(self, line):
        try:
            args = shlex.split(line)
            if not args:
                return True
            cmd, *rest = args
            if cmd == "quit" and not rest:
                self.say("Session closed.")
                return False
            if cmd == "help" and not rest:
                self.say(HELP)
            elif cmd == "manual" and not rest:
                self.say(MANUAL)
            elif cmd == "map" and not rest:
                self.graph()
            elif cmd == "sim" and not rest:
                self.say(f"SUPI: {SUPI}\nBilling plan: FREE\nSubscribed NSSAI: {FREE.snssai}\nDNN: internet")
            elif cmd == "slices" and not rest:
                self.say("NAME         SST   SD       DNN         SERVICE")
                for s, service in zip(SLICES, ("portal", "vault", "telemetry")):
                    self.say(f"{s.name:<12} {s.sst:<5} {s.sd:<8} {s.dnn:<11} {service}")
            elif cmd == "register" and not rest:
                self.say(self.network.register(), "32")
                self.graph()
            elif cmd == "authorize" and len(rest) == 3:
                self.say(self.network.authorize(*slice_args(rest)), "32")
                self.graph()
            elif cmd == "session" and len(rest) == 1:
                self.say(self.network.session(rest[0]), "32")
                self.graph()
            elif cmd == "surf" and len(rest) == 1:
                self.say(self.network.surf(rest[0]), "32")
                if rest[0] == "vault":
                    self.say(self.flag, "1;32")
            elif cmd == "ticket" and rest == ["export"]:
                self.say("TICKET " + self.network.export_ticket())
            elif cmd == "ticket" and len(rest) == 2 and rest[0] == "import":
                self.say(self.network.import_ticket(rest[1]), "32")
            elif cmd == "plan" and len(rest) == 4 and rest[0] == "create":
                self.say("PLAN " + self.network.plan_create(*slice_args(rest[1:])))
            elif cmd == "plan" and len(rest) == 2 and rest[0] == "show":
                self.say(json.dumps(self.network.plan_status(rest[1]), sort_keys=True))
            elif cmd == "plan" and len(rest) == 2 and rest[0] == "check":
                self.say("APPROVAL " + self.network.plan_check(rest[1]))
            elif cmd == "plan" and len(rest) == 5 and rest[0] == "edit":
                self.say(self.network.plan_edit(rest[1], *slice_args(rest[2:])))
            elif cmd == "plan" and len(rest) == 2 and rest[0] == "commit":
                self.say(self.network.plan_commit(rest[1]), "32")
                self.graph()
            elif cmd == "trace" and not rest:
                self.say("\n".join(self.network.events) or "No control-plane events yet.", "33")
            elif cmd == "status" and not rest:
                n = self.network
                self.say(f"Registered: {n.registered}\nSubscription: FREE\n"
                         f"Requested: {n.requested.snssai if n.requested else '-'}\n"
                         f"Authorized: {n.authorized.snssai if n.authorized else '-'}\n"
                         f"Active route: {n.active.snssai if n.active else '-'}\n"
                         f"Broker scope: {'handover' if n.handover else 'inspect'}\n"
                         f"Plans staged: {len(n.plans)}\n"
                         f"Vault reached: {n.completed}")
            elif cmd == "evidence" and not rest:
                self.say(json.dumps(self.network.evidence(), sort_keys=True))
            elif cmd == "color" and rest in (["on"], ["off"]):
                self.color = rest == ["on"]
                self.say("Color " + rest[0] + ".")
            elif cmd == "reset" and not rest:
                self.network = Network(secure=self.network.secure)
                self.say("SIM context, keys, plans and PDU session reset.")
                self.graph()
            else:
                raise ValueError("Unknown command or arguments. Type help for syntax.")
        except (ValueError, Denied) as error:
            self.say(str(error), "31")
        return True


def timeout_handler(signum, frame):
    raise TimeoutError


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--secure", action="store_true", help="Organizer-only fixes for both handover boundaries")
    parser.add_argument("--flag-file", type=Path, default=Path(__file__).with_name("flag.txt"))
    args = parser.parse_args()
    # DynamicContainer injects a team-specific flag; the file is only a local fallback.
    flag = os.environ.get("GZCTF_FLAG", "").strip()
    if not flag:
        flag = args.flag_file.read_text().strip()
    if not flag or "\n" in flag:
        raise SystemExit("Flag file must contain one nonempty line.")
    console = Console(flag, secure=args.secure)
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(SESSION_SECONDS)
    try:
        console.banner()
        for _ in range(MAX_COMMANDS):
            console.output.write("nr-ue> ")
            console.output.flush()
            raw = sys.stdin.buffer.readline(MAX_LINE + 1)
            if not raw:
                return
            if len(raw) > MAX_LINE:
                console.say("Input limit exceeded. Session closed.")
                return
            try:
                line = raw.decode("utf-8").rstrip("\r\n")
            except UnicodeDecodeError:
                console.say("Input must be UTF-8 text.")
                continue
            if any(ord(c) < 32 or ord(c) == 127 for c in line):
                console.say("Control characters are not accepted.")
                continue
            if not console.execute(line):
                return
        console.say("Command budget exhausted. Reconnect for a new session.")
    except TimeoutError:
        console.say("Session expired. Reconnect for a new SIM context.")
    except (BrokenPipeError, ConnectionResetError):
        # Avoid a second broken-pipe exception when Python flushes stdout at exit.
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
    finally:
        signal.alarm(0)


if __name__ == "__main__":
    main()
