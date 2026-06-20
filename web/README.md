# web/

TypeScript workspace (pnpm) for the API gateway and public portal (ADR-0002).
Gateway/portal are **presentation & orchestration only — no scoring** (scoring
lives in the Python Trust Engine; INV-DETERMINISM).

## Packages
| Package | Role | Status |
|---------|------|--------|
| `packages/contracts` (`@eip/contracts`) | TS types generated from `contracts/*.schema.json` (ADR-0004) | done |
| `api-gateway` (`@eip/api-gateway`) | Fastify HTTP entry: auth/routing/orchestration | health + info + `/v1/extract` (→ Claim) + `/v1/gather` (→ Evidence) + `/v1/score` (→ Trust) proxies |
| `portal` (`@eip/portal`) | Next.js public transparency UI | VerdictCard; fetches live verdict from gateway (`GATEWAY_URL`) with static fallback |

## Common tasks (run from repo root)
```bash
pnpm install
pnpm dev               # boot the FULL stack (engines + gateway :4000 + portal :3000)
pnpm gen:contracts     # regenerate @eip/contracts TS types from ../contracts
pnpm -r typecheck
pnpm -r test
pnpm --filter @eip/portal dev          # portal only (sample-data fallback)
pnpm --filter @eip/api-gateway start   # run the gateway (PORT, default 3000)
```
`pnpm dev` wraps `scripts/dev.sh` — Ctrl-C stops everything. The gateway runs on
:4000 to avoid colliding with the portal on :3000.

Generated files under `packages/contracts/src/` are do-not-edit — change the JSON
Schema in `contracts/` and rerun `pnpm gen:contracts`.
