#!/usr/bin/env python3

import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

PAGE = 2048
OOB = 64
ZIP_PASS = b"hololive_apanya_hology_bang"


def run(*cmd, check=True, binary=False):
    kw = {"check": check, "capture_output": True}
    if not binary:
        kw["text"] = True
    return subprocess.run(cmd, **kw)


def strip_oob(src, dst):
    with open(src, "rb") as f:
        raw = f.read()
    data = b"".join(raw[i:i + PAGE] for i in range(0, len(raw), PAGE + OOB))
    with open(dst, "wb") as f:
        f.write(data)


def main(source):
    work = tempfile.mkdtemp(prefix="hology9-solve-")
    print(f"[+] Workspace: {work}")

    flash = os.path.join(work, "flash.bin")
    if source.endswith(".zip"):
        with zipfile.ZipFile(source) as z:
            z.extractall(work, pwd=ZIP_PASS)
        for root, _, files in os.walk(work):
            if "flash.bin" in files:
                shutil.copy(os.path.join(root, "flash.bin"), flash)
                break
    else:
        shutil.copy(source, flash)

    image = os.path.join(work, "image.bin")
    strip_oob(flash, image)
    print(f"[+] Stripped OOB: {os.path.getsize(image)} bytes")

    parts = {
        "env":   (3072,  256),
        "root":  (4096,  8192),
        "nvram": (12288, 1024),
        "user":  (13312, 18432),
    }
    for name, (skip, count) in parts.items():
        run("dd", f"if={image}", f"of={work}/{name}.bin",
            "bs=512", f"skip={skip}", f"count={count}", "status=none")

    keyseed = re.search(
        r"^keyseed=([0-9a-f]+)$",
        run("strings", f"{work}/env.bin").stdout, re.M).group(1)
    print(f"[+] keyseed: {keyseed}")

    fls = run("fls", "-r", "-p", f"{work}/user.bin").stdout
    inodes = {}
    for line in fls.splitlines():
        parts_ = line.split()
        if len(parts_) >= 2 and parts_[0].startswith("r/"):
            path = " ".join(parts_[2:])
            inode = parts_[1].rstrip(":")
            if "bootlog.txt" in path:
                inodes["bootlog"] = inode
            if "capture.pcap" in path:
                inodes["pcap"] = inode

    bootlog = run("icat", f"{work}/user.bin", inodes["bootlog"]).stdout
    cpu_id = re.search(r"CPU:\s*serial\s+([0-9A-F]+)", bootlog).group(1)
    print(f"[+] CPU_ID: {cpu_id}")

    huk = hashlib.sha256((cpu_id + keyseed).encode()).hexdigest()
    print(f"[+] HUK: {huk}")

    # Trim IV + trailing 0x00 padding to isolate ciphertext.
    # (openssl `-iflag skip_bytes=` needs openssl >= 3.2; Ubuntu 24.04 ships 3.0.)
    with open(f"{work}/nvram.bin", "rb") as f:
        nvram_bytes = f.read()
    iv_hex = nvram_bytes[:16].hex()
    end = len(nvram_bytes)
    while end > 16 and nvram_bytes[end - 1] == 0:
        end -= 1
    with open(f"{work}/body.enc", "wb") as f:
        f.write(nvram_bytes[16:end])

    subprocess.run(
        ["openssl", "enc", "-aes-256-cbc", "-d",
         "-K", huk, "-iv", iv_hex,
         "-in", f"{work}/body.enc", "-out", f"{work}/nvram.dec"],
        check=True, capture_output=True,
    )

    psk_hex = re.search(
        r"^psk_hex=([0-9a-f]+)$",
        open(f"{work}/nvram.dec").read(), re.M).group(1)
    print(f"[+] psk_hex: {psk_hex}")

    pcap = f"{work}/capture.pcap"
    with open(pcap, "wb") as f:
        f.write(run("icat", f"{work}/user.bin", inodes["pcap"],
                    binary=True).stdout)

    tshark_out = run(
        "tshark", "-r", pcap,
        "-o", f"tls.psk:{psk_hex}",
        "-Y", "mqtt",
        "-T", "fields", "-e", "mqtt.msg",
    ).stdout

    hex_stream = tshark_out.replace(":", "").replace("\n", "").strip()
    payload = bytes.fromhex(hex_stream)
    flag = re.search(rb"HOLOGY9\{[^}]+\}", payload).group(0).decode()
    print(f"[+] FLAG: {flag}")
    return flag


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: solve.py <flash.bin | attachment.zip>", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1])
