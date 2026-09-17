from pathlib import Path
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIServer, make_server
import html
import os
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
NAME = os.environ.get("CHALLENGE_NAME", "Receipt")
PORT = int(os.environ.get("PORT", "8000"))
OUTPUT = ROOT / "output.txt"
FILES = {
    "/challenge.py": ROOT / "challenge.py",
    "/description.txt": ROOT / "description.txt",
    "/output.txt": OUTPUT,
}


class Threaded(ThreadingMixIn, WSGIServer):
    daemon_threads = True
    allow_reuse_address = True


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


def page():
    title = html.escape(NAME)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    body {{ margin: 0; font-family: system-ui, sans-serif; background: #10141d; color: #eef3f8; }}
    main {{ width: min(760px, calc(100vw - 32px)); margin: 48px auto; }}
    a {{ color: #8fd3ff; }}
    .box {{ border: 1px solid #334155; border-radius: 8px; padding: 20px; background: #151c28; }}
    li {{ margin: 10px 0; }}
  </style>
</head>
<body>
  <main>
    <h1>{title}</h1>
    <div class="box">
      <p>Download the generated handout for this container.</p>
      <ul>
        <li><a href="/description.txt">description.txt</a></li>
        <li><a href="/challenge.py">challenge.py</a></li>
        <li><a href="/output.txt">output.txt</a></li>
      </ul>
    </div>
  </main>
</body>
</html>
"""


def send(start, status, body, mime):
    start(status, [("Content-Type", mime), ("Cache-Control", "no-store")])
    if isinstance(body, str):
        body = body.encode()
    return [body]


def app(environ, start):
    path = environ.get("PATH_INFO", "/")
    if path == "/":
        return send(start, "200 OK", page(), "text/html; charset=utf-8")
    if path in FILES and FILES[path].is_file():
        return send(
            start,
            "200 OK",
            FILES[path].read_bytes(),
            "text/plain; charset=utf-8",
        )
    return send(start, "404 Not Found", "missing\n", "text/plain; charset=utf-8")


def main():
    make()
    with make_server("0.0.0.0", PORT, app, server_class=Threaded) as server:
        print(f"serving http://0.0.0.0:{PORT}", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
