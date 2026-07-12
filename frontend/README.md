# InsightBoard frontend

React (Vite) customer dashboard. Consumes the FastAPI analytics API.

## Run

```bash
cp .env.example .env
npm install
npm run dev
```

Requires the backend at `VITE_API_URL` (default `http://localhost:8000`).

Optional: `VITE_ANALYTICS_URL` for the “Analyst view” link (default `http://localhost:8000/analytics/`).

Deploy: set `VITE_API_URL` on Vercel; see root `DEPLOYMENT.md` and `vercel.json`.

## Scripts

- `npm run dev` — local Vite server
- `npm run build` — production bundle to `dist/`
- `npm run preview` — preview production build
