# KittenVault — CTF Writeup (Android Reverse Engineering)

**Kategori:** Reverse Engineering (Android / JNI)
**Difficulty:** Easy
**File:** `KittenVault.apk` (`com.hology.kitten`)

---

## 1. TL;DR

Aplikasi memiliki **3 string berformat flag**, tetapi hanya 1 yang asli. UI login selalu menampilkan dialog error. Flag asli dicetak ke `logcat` saat kredensial yang divalidasi oleh `libvault_core.so` dimasukkan dengan benar.

* **Username:** `adminaseli`
* **Password:** `k1tt3n5`
* **Real Flag:** `HOLOGY9{r34L_c0R3_M3m0Ry_m4N1pUlaT1oN_2E9CE}`

---

## 2. Analisis Alur Java

Decompile APK menggunakan JADX / Androguard untuk memetakan alur utama:

1. **`MainActivity.onCreate()`**
Memanggil `cryptoHelper.getSecretKey()` yang mencetak decoy flag ke logcat (`VAULT_SYSTEM`).

2. **`btnLogin.setOnClickListener()`**
* Memanggil `cryptoHelper.checkCredentials(user, pass)` (`libvault_core.so`).
* Jika kredensial valid, flag asli langsung dicetak ke logcat (`VAULT_SUCCESS`).
* Aplikasi kemudian memeriksa `SharedPreferences` dan selalu memunculkan dialog error (`Login Failed` / `Error 404`).

3. **`LogcatService`**
Dipicu saat register/login via `SharedPreferences`. Mencetak decoy flag kedua yang mengonfirmasi bahwa flag cat/service adalah palsu.

---

## 3. Analisis Native Library

### Decoy Flags (Palsu)

* **`libvault_sec.so` (`getSecretKey`):** XOR `0x55` pada array `.data` $\rightarrow$ `HOLOGY9{f4Ke_fL4g_Fr0m_l1br4Ry_s3C_h3He}`
* **`LogcatService.java`:** XOR `0x43` pada byte array $\rightarrow$ `HOLOGY9{f4K3_c4T_iS_N0t_s4m3_Wi7h_k1Tt3n_FL4g}`

### Core Validation (`libvault_core.so`)

#### A. Username Validation (`validate_username`)

Syarat panjang 10 karakter. Menggunakan XOR berantai dengan nilai awal `0x55` dan array target `u_seq`:

* `u[0] ^ 0x55 == 0x34` $\rightarrow$ `'a'`
* `u[i] = u[i-1] ^ u_seq[i]` $\rightarrow$ **`adminaseli`**

#### B. Password Validation (`validate_password`)

Syarat panjang 7 karakter. Menggunakan 6 persamaan matematika:

1. `p[0] ^ 0x77 = 0x1C` $\rightarrow$ `'k'`
2. `p[0] + p[1] = 156` $\rightarrow$ `'1'`
3. `p[2] - p[1] = 67` $\rightarrow$ `'t'`
4. `p[2] ^ p[3] = 0` $\rightarrow$ `'t'`
5. `p[3] + p[4] = 167` $\rightarrow$ `'3'`
6. `p[4] ^ p[5] = 93` $\rightarrow$ `'n'`
7. `p[5] - p[6] = 57` $\rightarrow$ `'5'`

* Result $\rightarrow$ **`k1tt3n5`**

#### C. Flag Reconstruction (`reconstruct_flag`)

Dekripsi 44-byte array dari `.data` (`DAT_00108f40`) menggunakan rumus:


$$\text{Flag}[i] = \text{g\_flag\_data}[i] \oplus i \oplus \text{Password}[i \pmod 7]$$

---

## 4. Standalone Solver Script

```python
u_seq = [0x34, 0x05, 0x09, 0x04, 0x07, 0x0f, 0x12, 0x16, 0x09, 0x05]
p_seq = [0x1C, 156, 67, 0, 167, 93, 57]
g_flag_data = [
    0x23, 0x7f, 0x3a, 0x38, 0x70, 0x32, 0x0a, 0x17,
    0x4b, 0x4e, 0x4a, 0x74, 0x3d, 0x5b, 0x55, 0x6c,
    0x57, 0x3a, 0x6c, 0x4e, 0x4c, 0x4e, 0x75, 0x1a,
    0x33, 0x47, 0x40, 0x60, 0x46, 0x5c, 0x3f, 0x07,
    0x72, 0x1b, 0x26, 0x27, 0x5b, 0x0e, 0x60, 0x51,
    0x7f, 0x5f, 0x04, 0x67
]

# 1. Solve Username
user = [u_seq[0] ^ 0x55]
for i in range(1, 10):
    user.append(user[i - 1] ^ u_seq[i])
username = "".join(chr(c) for c in user)

# 2. Solve Password
p = [0] * 7
p[0] = p_seq[0] ^ 0x77
p[1] = p_seq[1] - p[0]
p[2] = p_seq[2] + p[1]
p[3] = p_seq[3] ^ p[2]
p[4] = p_seq[4] - p[3]
p[5] = p_seq[5] ^ p[4]
p[6] = p[5] - p_seq[6]
password = "".join(chr(c) for c in p)

# 3. Reconstruct Flag
flag = "".join(chr(g_flag_data[i] ^ i ^ ord(password[i % 7])) for i in range(len(g_flag_data)))

print(f"[+] Username : {username}")
print(f"[+] Password : {password}")
print(f"[+] Real Flag: {flag}")

```

---