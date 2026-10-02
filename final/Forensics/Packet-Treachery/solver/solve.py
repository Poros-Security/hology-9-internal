#!/usr/bin/env python3
"""
Reference solver for Packet Treachery.

Dependencies:
    pip install pyshark   (plus `tshark` on PATH)

Usage:
    python3 solve.py [--pcap PATH] [--host HOST] [--port PORT]
"""

import argparse
import hashlib
import re
import socket
import sys
from pathlib import Path


DEFAULT_PCAP = Path(__file__).resolve().parent.parent / "dist" / "incident.pcapng"
GATE_HOST    = "127.0.0.1"
GATE_PORT    = 11133


def extract(pcap_path: Path):
    import pyshark

    attacker_ip = broker_ip = None
    xml_bytes = None
    exfil_bytes = None
    broker_version = None

    cap = pyshark.FileCapture(str(pcap_path), display_filter="tcp", keep_packets=False)
    flows = {}
    for pkt in cap:
        if "TCP" not in pkt:
            continue
        try:
            sid = int(pkt.tcp.stream)
        except AttributeError:
            continue
        if not hasattr(pkt.tcp, "payload") or pkt.tcp.payload is None:
            continue
        hexbytes = bytes.fromhex(pkt.tcp.payload.replace(":", ""))
        if not hexbytes:
            continue
        key = (pkt.ip.src, pkt.tcp.srcport, pkt.ip.dst, pkt.tcp.dstport)
        flows.setdefault(sid, []).append((key, hexbytes))
    cap.close()

    for sid, frames in flows.items():
        if not frames:
            continue
        all_bytes = b"".join(b for _, b in frames)

        if b"ClassPathXmlApplicationContext" in all_bytes:
            attacker_ip = frames[0][0][0]
            broker_ip   = frames[0][0][2]
        if b"5.15.9" in all_bytes and broker_version is None:
            m = re.search(rb"5\.1[0-9]\.[0-9]+", all_bytes)
            if m:
                broker_version = m.group(0).decode()
        if b"GET /poc.xml" in all_bytes:
            for (src, sp, dst, dp), body in frames:
                if b"HTTP/1." in body and b"<?xml" in body:
                    header, _, xml = body.partition(b"\r\n\r\n")
                    xml_bytes = xml.rstrip()
        if any(k[3] == "4444" for k, _ in frames):
            exfil = b"".join(body for (src, sp, dst, dp), body in frames if dp == "4444")
            if exfil:
                exfil_bytes = exfil

    if attacker_ip is None or broker_ip is None:
        print("[-] could not locate exploit frame", file=sys.stderr); sys.exit(1)
    if xml_bytes is None or exfil_bytes is None:
        print("[-] could not locate xml or exfil", file=sys.stderr); sys.exit(1)

    return {
        "attacker_ip":    attacker_ip,
        "broker_ip":      broker_ip,
        "broker_version": broker_version or "5.15.9",
        "xml":            xml_bytes,
        "exfil":          exfil_bytes,
    }


def recv_until(sock, needle, timeout=5.0):
    sock.settimeout(timeout)
    buf = b""
    while needle not in buf:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buf += chunk
    return buf


def send_line(sock, s):
    sock.sendall((s + "\n").encode())


def solve(pcap_path, host, port):
    ex = extract(pcap_path)
    xml   = ex["xml"]
    exfil = ex["exfil"]
    xml_sha   = hashlib.sha256(xml).hexdigest()
    exfil_sha = hashlib.sha256(exfil).hexdigest()
    print(f"[*] attacker ip:    {ex['attacker_ip']}")
    print(f"[*] broker ip:      {ex['broker_ip']}")
    print(f"[*] broker version: {ex['broker_version']}")
    print(f"[*] xml sha256:     {xml_sha}")
    print(f"[*] exfil sha256:   {exfil_sha}")

    values = re.findall(rb"<value>(.*?)</value>", xml, re.DOTALL)
    assert len(values) == 3
    shell_bin = values[0].decode().strip()
    full_cmd  = values[2].decode().strip().replace("&gt;", ">")

    m = re.search(rb"api\.token=(\S+)", exfil)
    assert m
    api_token = m.group(1).decode()

    answers = [
        "CVE-2023-46604", "10.0", "Apache ActiveMQ", "OpenWire", "61616",
        ex["broker_version"], ex["attacker_ip"], ex["broker_ip"],
        "org.springframework.context.support.ClassPathXmlApplicationContext",
        f"http://{ex['attacker_ip']}:8000/poc.xml",
        xml_sha, "java.lang.ProcessBuilder", shell_bin, full_cmd,
        "4444", "/opt/activemq/conf/credentials.properties",
        exfil_sha, api_token,
    ]
    assert len(answers) == 18

    s = socket.create_connection((host, port), timeout=10)
    print(f"[*] connected to gate at {host}:{port}")
    for ans in answers:
        prompt = recv_until(s, b"Answer> ")
        sys.stdout.write(prompt.decode(errors="replace")); sys.stdout.flush()
        print(f"<<< {ans}")
        send_line(s, ans)

    s.settimeout(3.0)
    try:
        while True:
            chunk = s.recv(4096)
            if not chunk: break
            sys.stdout.write(chunk.decode(errors="replace")); sys.stdout.flush()
    except socket.timeout:
        pass
    s.close()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--pcap", default=str(DEFAULT_PCAP))
    p.add_argument("--host", default=GATE_HOST)
    p.add_argument("--port", type=int, default=GATE_PORT)
    args = p.parse_args()
    solve(Path(args.pcap), args.host, args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
