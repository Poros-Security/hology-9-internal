from pathlib import Path
from socketserver import StreamRequestHandler, TCPServer, ThreadingMixIn
import os
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
PORT = int(os.environ.get("PORT", "8000"))
OUTPUT = ROOT / "output.txt"


class Threaded(ThreadingMixIn, TCPServer):
    daemon_threads = True
    allow_reuse_address = True


class Handler(StreamRequestHandler):
    def handle(self):
        data = OUTPUT.read_bytes()
        self.wfile.write(data)
        if not data.endswith(b"\n"):
            self.wfile.write(b"\n")


def make():
    flag = (
        os.environ.get("GZCTF_FLAG")
        or os.environ.get("FLAG")
        or "HOLOGY9{receipt_local}"
    )
    env = os.environ.copy()
    env["GZCTF_FLAG"] = flag
    env["FLAG"] = flag
    result = subprocess.run(
        [sys.executable, "challenge.py"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        check=True,
        timeout=120,
    )
    OUTPUT.write_bytes(result.stdout)


def main():
    make()
    with Threaded(("0.0.0.0", PORT), Handler) as server:
        print(f"serving tcp://0.0.0.0:{PORT}", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
