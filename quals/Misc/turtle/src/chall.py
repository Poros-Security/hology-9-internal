#!/usr/bin/env python3

import os
import signal
import sys
import unicodedata


TIMEOUT_SECONDS = 300

# Flag berasal dari environment GZCTF.
FLAG = os.environ.get(
    "GZCTF_FLAG",
    "HOLOGY9{LOCAL_TEST_FLAG}"
)


QUESTIONS = [
    {
        "question": (
            "[1/6] Latitude dan Longitude dari lokasi pada bukti? [e.g. 'X.XXX, Y.YYY'](minimal 3 angka di belakang koma)\n"
            "> "
        ),
        "answers": [
            "-8.324, 112.203",
            "-8.3243, 112.2033",
            "-8.324335770892482, 112.20329506138158",
        ],
    },
    {
        "question": (
            "[2/6] Pantai itu memiliki desa tetangga yang sedang mengalami masalah politik. Apakah desa itu?\n"
            "> "
        ),
        "answers": [
            "Serang",
            "Desa Serang",
            "desa serang",
            "serang",
        ],
    },
    {
        "question": (
            "[3/6] Siapa kepala desanya? (nama lengkap)\n"
            "> "
        ),
        "answers": [
            "Dwi Handoko",
            "dwi handoko",
        ],
    },
    {
        "question": (
            "[4/6] Di ujung desa tersebut terdapat konsolidasi pergerakan bawah tanah para oposisi pejabat. Apa nama warung kopi tersebut?\n"
            "> "
        ),
        "answers": [
            "Dikasih Kopi",
            "dikasih kopi",
        ],
    },
    {
        "question": (
            "[5/6] Siapa pemilik tempat itu?\n"
            "> "
        ),
        "answers": [
            "dita faisal",
            "Dita Faisal",
            "endik koeswoyo",
            "Endik Koeswoyo",
        ],
    },
    {
        "question": (
            "[6/6] Nama komunitas oposisi tersebut\n"
            "> "
        ),
        "answers": [
            "Forum Pemuda Peduli Serang",
            "forum pemuda peduli serang",
        ],
    },
]


def normalize(value):
    value = unicodedata.normalize("NFKC", value)
    value = value.strip().lower()
    value = " ".join(value.split())
    return value


def timeout_handler(signum, frame):
    print("\n[!] Session timed out.")
    sys.exit(0)


def ask_question(question_data):
    print(question_data["question"], end="", flush=True)

    answer = sys.stdin.readline()

    if not answer:
        print("\n[!] Connection closed.")
        sys.exit(0)

    answer = normalize(answer)

    valid_answers = {
        normalize(item)
        for item in question_data["answers"]
    }

    return answer in valid_answers


def main():
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(TIMEOUT_SECONDS)

    print("=" * 60)
    print("                 OSINT CASE FILE")
    print("=" * 60)
    print()
    print("Solve all questions to obtain the flag.")
    print("Answers are case-insensitive.")
    print()

    for question_data in QUESTIONS:
        while True:
            if ask_question(question_data):
                print("[+] Correct!\n")
                break

            print("[-] Incorrect. Try again.\n")

    print("=" * 60)
    print("CASE SOLVED")
    print("=" * 60)
    print()
    print(f"FLAG: {FLAG}")
    print()


if __name__ == "__main__":
    main()
