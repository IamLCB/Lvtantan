# Lvtantan Backend

## Run locally

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`.

## Test

```bash
.venv/bin/pytest -v
```

## Manual API check

```bash
curl -s http://127.0.0.1:8000/health
```
