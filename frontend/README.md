# InsightBoard frontend

React (Vite) customer dashboard. Consumes the FastAPI analytics API.

## Run

```bash
cp .env.example .env
npm install
npm run dev
```

Requires the backend at `VITE_API_URL` (default `http://localhost:8000`).

## Scripts

- `npm run dev` — local Vite server
- `npm run build` — production bundle to `dist/`
- `npm run preview` — preview production build
