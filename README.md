# InsightBoard

Full-stack analytics dashboard: upload a CSV (or load a sample sales dataset), clean it with pandas, serve analytics over a FastAPI REST API, and view the same data in a polished React dashboard and a Dash/Plotly analyst page. Google OAuth protects the app; PostgreSQL stores users and datasets.

## Architecture

```
PostgreSQL  →  FastAPI (auth, upload, analytics)
                    │                    │
              React (Vercel)        Dash (@ /analytics on Azure)
```

Both frontends share the **same** API — API-first design.

## Repo layout

| Path | Role |
|------|------|
| `backend/` | FastAPI + pandas + SQLAlchemy + Dash |
| `frontend/` | React (Vite) customer dashboard |
| `sample_data/` | Demo sales CSV |
| `scripts/` | `start-db.sh`, `smoke-test.sh` |
| `DEPLOYMENT.md` | Azure + Vercel (and AWS notes) |
| `doc/` | Local learning notes (gitignored) |

## API surface

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness |
| GET | `/api/db/health` | Postgres check |
| GET | `/api/auth/google/login` | Start Google OAuth |
| POST | `/api/auth/dev-login` | Local JWT (disable in prod) |
| GET | `/api/auth/me` | Current user |
| POST | `/api/datasets/upload` | CSV upload |
| POST | `/api/datasets/sample` | Load sample sales |
| GET | `/api/data/{id}/summary` | KPIs |
| GET | `/api/data/{id}/trends` | Time series |
| GET | `/api/data/{id}/breakdown` | Category/region bars |
| UI | `/analytics/` | Dash analyst workspace |

Interactive docs: http://localhost:8000/docs

## Quick start (local)

### 1. PostgreSQL

```bash
chmod +x scripts/start-db.sh scripts/smoke-test.sh
./scripts/start-db.sh
```

### 2. Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
cd backend
uvicorn app.main:app --reload --port 8000
```

Optional smoke test (another terminal): `./scripts/smoke-test.sh`

### 3. React

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Open http://localhost:5173 → **Dev login** → **Load sample sales**.

Dash analyst UI: http://localhost:8000/analytics/ (paste the same JWT).

### Compose (API + DB)

```bash
docker compose up --build
```

### 3. Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Open http://localhost:5173 — use **Dev login**, then **Load sample sales**.

Analyst (Dash) view on the same backend: http://localhost:8000/analytics/

## License

MIT
