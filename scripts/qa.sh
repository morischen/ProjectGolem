#!/usr/bin/env bash
#
# Repo-wide QA gate for the loop-engineering framework: lint + typecheck + tests +
# runtime smoke for every service. Run after each loop before commit (CLAUDE.md §2).
# Exits non-zero on the first failure.
#
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"

# Python services expose a `make qa` target (lint + typecheck + test + smoke).
PY_SERVICES=(
  "ai-services/trust-engine"
  "ai-services/claim-engine"
  "ai-services/evidence-engine"
  "ai-services/e2e"
)

for svc in "${PY_SERVICES[@]}"; do
  echo "==================================================================="
  echo "QA: $svc"
  echo "==================================================================="
  ( cd "$root/$svc" && make qa )
done

# TypeScript workspace (web/): typecheck + tests + format check.
if [ -f "$root/pnpm-workspace.yaml" ]; then
  echo "==================================================================="
  echo "QA: web (pnpm workspace)"
  echo "==================================================================="
  ( cd "$root" && pnpm -r typecheck && pnpm -r test && pnpm format:check )
fi

echo
echo "✅ ALL QA PASSED"
