#!/usr/bin/env bash
#
# Boot the full EIP dev stack on fixed ports. Ctrl-C stops everything.
#
#   trust-engine     :8000   (FastAPI)
#   claim-engine     :8001   (FastAPI)
#   evidence-engine  :8002   (FastAPI)
#   api-gateway      :4000   (Fastify; proxies to the engines above)
#   portal           :3000   (Next.js, public; points at the gateway on :4000)
#   admin            :3001   (Next.js, admin; points at the gateway on :4000)
#
# The gateway runs on :4000 (not :3000) so it doesn't collide with the portal.
# Requires uv and pnpm (ADR-0002). Run from anywhere:  bash scripts/dev.sh
#
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"

# Load local dev credentials/config (gitignored). See .env.example.
if [ -f "$root/.env" ]; then
  echo "→ loading $root/.env"
  set -a
  # shellcheck disable=SC1091
  . "$root/.env"
  set +a
fi

pids=()

cleanup() {
  echo
  echo "stopping EIP dev stack…"
  for pid in "${pids[@]}"; do kill "$pid" 2>/dev/null || true; done
  pkill -P $$ 2>/dev/null || true
}
trap cleanup EXIT INT TERM

start() {
  local label="$1" dir="$2"
  shift 2
  echo "→ starting $label"
  ( cd "$root/$dir" && exec "$@" ) &
  pids+=("$!")
}

start "trust-engine    :8000" ai-services/trust-engine \
  uv run uvicorn eip_trust.api:app --port 8000
start "claim-engine    :8001" ai-services/claim-engine \
  uv run uvicorn eip_claim.api:app --port 8001
start "evidence-engine :8002" ai-services/evidence-engine \
  uv run uvicorn eip_evidence.api:app --port 8002
PORT=4000 start "api-gateway     :4000" web/api-gateway \
  pnpm start
GATEWAY_URL=http://localhost:4000 start "portal          :3000" web/portal \
  pnpm dev
NEXT_PUBLIC_GATEWAY_URL=http://localhost:4000 start "admin           :3001" web/admin \
  pnpm dev --port 3001

echo
echo "EIP dev stack up → portal: http://localhost:3000  admin: http://localhost:3001  (gateway :4000, engines :8000/:8001/:8002)"
echo "Press Ctrl-C to stop."
wait
