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
)

for svc in "${PY_SERVICES[@]}"; do
  echo "==================================================================="
  echo "QA: $svc"
  echo "==================================================================="
  ( cd "$root/$svc" && make qa )
done

echo
echo "✅ ALL QA PASSED"
