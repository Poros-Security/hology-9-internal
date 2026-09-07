# Compliant

The compliance team built a document intake portal with a reviewer bot and a file upload form.

Players receive the source archive from `dist/` and interact with the deployed HTTPS service. The intended path is to abuse the document review flow to recover the reviewer secret, then submit it to `/flag`.

## Local Validation

```bash
cd Web/compliant/src
docker compose up -d --build
curl http://127.0.0.1:8443/
```

The solver can be run locally with:

```bash
cd Web/compliant
python3 solver/solve.py --target http://127.0.0.1:8443
```
