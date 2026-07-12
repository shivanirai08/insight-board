#!/usr/bin/env bash
# Quick API smoke test (Postgres + uvicorn must already be running).
set -euo pipefail

BASE="${1:-http://127.0.0.1:8000}"

echo "→ health"
curl -sf "$BASE/health" | tee /dev/stderr | grep -q '"status":"ok"'

echo "→ db health"
curl -sf "$BASE/api/db/health" | tee /dev/stderr | grep -q '"status":"ok"'

echo "→ dev login"
TOKEN=$(curl -sf -X POST "$BASE/api/auth/dev-login" \
  -H "Content-Type: application/json" \
  -d '{"email":"smoke@example.com","full_name":"Smoke"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo "→ sample dataset"
DID=$(curl -sf -X POST "$BASE/api/datasets/sample" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "→ summary for dataset $DID"
curl -sf "$BASE/api/data/$DID/summary" -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['row_count']>0; print('rows', d['row_count'], 'revenue', d['total_revenue'])"

echo "→ analytics page"
code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/analytics/")
test "$code" = "200"

echo "OK — smoke test passed"
