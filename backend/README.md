# InsightBoard backend

FastAPI application: OAuth, CSV ingestion, analytics endpoints, and Dash at `/analytics`.

## Prerequisites

Start PostgreSQL from the repo root:

```bash
./scripts/start-db.sh
```

## Run

From repo root (with venv activated):

```bash
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
uvicorn app.main:app --reload --app-dir backend --port 8000
```

Or from `backend/`:

```bash
uvicorn app.main:app --reload --port 8000
```

- Interactive API docs: http://localhost:8000/docs  
- DB check: http://localhost:8000/api/db/health  
- Dev login: `POST /api/auth/dev-login`  
- Google login: http://localhost:8000/api/auth/google/login (needs `.env` credentials)

Learning notes (local): `doc/04-oauth-jwt.md`
