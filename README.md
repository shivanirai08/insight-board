# InsightBoard

Full-stack analytics dashboard: upload a CSV (or load a sample sales dataset), clean it with pandas, serve analytics over a FastAPI REST API, and view the same data in a polished React dashboard and a Dash/Plotly analyst page. Google OAuth protects the app; PostgreSQL stores users and datasets.

## Architecture

```
PostgreSQL  →  FastAPI (auth, upload, /api/summary|trends|breakdown)
                    │                    │
              React (customer)      Dash (analyst @ /analytics)
```

Both frontends consume the **same** API — API-first design.

## Repo layout

| Path | Role |
|------|------|
| `backend/` | FastAPI + pandas + SQLAlchemy + Dash mount |
| `frontend/` | React (Vite) customer dashboard |
| `sample_data/` | Example sales CSV for demos |
| `doc/` | Local learning notes (gitignored — not in git) |

## Quick start (local)

### Backend

```bash
cd backend
python3 -m venv ../.venv
source ../.venv/bin/activate   # Windows: ..\.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # edit secrets as needed
uvicorn app.main:app --reload --port 8000
```

- API docs: http://localhost:8000/docs  
- Health: http://localhost:8000/health  

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the URL Vite prints (usually http://localhost:5173).

## License

MIT
