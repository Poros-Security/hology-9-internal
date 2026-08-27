# Waifu Love Calculator — Admin Notes

## GZCTF setup

This folder is a gzcli/GZCTF dynamic-container challenge root.

Expected layout:

```text
waifu-love-calculator/
├── challenge.yml
├── dist/
├── solver/
└── src/
```

`challenge.yml` uses:

```yaml
type: "DynamicContainer"
container:
  flagTemplate: "HOLOGY9{real_waifu_model_inversion_[TEAM_HASH]}"
  containerImage: "{{.slug}}:latest"
  exposePort: 5000
scripts:
  start: cd src && docker build -t {{.slug}} .
```

The app reads the dynamic flag from `GZCTF_FLAG` first, then `FLAG` as a fallback.

## Intended solve

1. Open the service.
2. Submit any valid pair, for example `AB + CD`.
3. Inspect the `/api/calculate` response instead of only the UI.
4. Notice high-precision fields:
   - `model_confidence`
   - `model_logit`
5. Use those fields as a black-box confidence oracle.
6. Search the four-letter space toward the highest logit until `WA + FU` is recovered.
7. Submit `WA + FU` to receive the GZCTF dynamic team flag.

The included solver performs a beam-search coordinate attack:

```bash
python solver/solve.py http://HOST:PORT
```

## ML design

The backend loads `src/model/waifu_model.npz` and performs real logistic-regression
inference using `src/ml_model.py`. The model was trained over all `26^4` possible
initial combinations using circular `sin/cos` letter embeddings.

The challenge is intentionally small and educational: it demonstrates how exposing
high-precision confidence/logit values can turn a model into an inversion oracle.

## Local testing

```bash
cd src
docker compose up --build
python ../solver/solve.py http://localhost:5000
```

The local compose file sets:

```text
GZCTF_FLAG=HOLOGY9{local_dynamiccontainer_test}
SECRET_A=WA
SECRET_B=FU
```
