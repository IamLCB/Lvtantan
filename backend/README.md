# Lvtantan Backend

FastAPI backend skeleton for the Lvtantan shared travel expense app.

## Setup

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Run Tests

```bash
.venv/bin/pytest tests/test_health.py -v
```

## Run API

```bash
.venv/bin/uvicorn app.main:app --reload
```
