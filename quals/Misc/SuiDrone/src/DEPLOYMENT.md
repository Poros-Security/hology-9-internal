# DynamicContainer deployment

GZCTF creates one SuiDrone container per team and injects that team's dynamic
flag as `GZCTF_FLAG`. No game public key, team allowlist, static flag, shared
database, or participant token is used.

The canonical deployment command is in `challenge.yml`:

```sh
cd src && docker build -t {{.slug}} .
```

GZCTF must expose container port `8787`. The player starts the downloaded
client with the instance IP and port supplied by GZCTF:

```sh
./suidrone --server http://INSTANCE_IP:PORT --allow-insecure-http
```

For a local smoke test only:

```sh
GZCTF_FLAG='HOLOGY9{suidrone_local_dynamic_test}' docker compose up --build
curl http://127.0.0.1:8787/health
```

The client archive remains flag-free. Do not set `GZCTF_FLAG` in committed
files; GZCTF supplies it for each DynamicContainer.
