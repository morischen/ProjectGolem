# web/

TypeScript workspace (pnpm) for the API gateway and public portal (ADR-0002).
Gateway/portal are **presentation & orchestration only — no scoring** (scoring
lives in the Python Trust Engine; INV-DETERMINISM).

## Packages
| Package | Role | Status |
|---------|------|--------|
| `packages/contracts` (`@eip/contracts`) | TS types generated from `contracts/*.schema.json` (ADR-0004) | done |
| `api-gateway` (`@eip/api-gateway`) | Fastify HTTP entry: auth/routing/orchestration | health + info + `/v1/extract` (→ Claim) + `/v1/gather` (→ Evidence) + `/v1/score` (→ Trust). Proxy routes are API-key-protected (scopes) + rate-limited |
| `portal` (`@eip/portal`) | Next.js public transparency UI | VerdictCard; fetches live verdict from gateway (`GATEWAY_URL`) with static fallback |

## Common tasks (run from repo root)
```bash
cp .env.example .env   # then fill in OPENROUTER_API_KEY (see .env.example); .env is gitignored
pnpm install
pnpm dev               # boot the FULL stack (engines + gateway :4000 + portal :3000); loads .env
pnpm gen:contracts     # regenerate @eip/contracts TS types from ../contracts
pnpm -r typecheck
pnpm -r test
pnpm --filter @eip/portal dev          # portal only (sample-data fallback)
pnpm --filter @eip/api-gateway start   # run the gateway (PORT, default 3000)
```
`pnpm dev` wraps `scripts/dev.sh` — Ctrl-C stops everything. The gateway runs on
:4000 to avoid colliding with the portal on :3000.

**Gateway auth/limits:** the `/v1/*` proxy routes require an API key with the
`write` scope and are rate-limited. Configure keys via `EIP_API_KEYS`
(`"k1:write read; k2:read"`); with no keys set, auth is disabled (dev mode). Send
`x-api-key: <key>`. (API keys are the first cut; OIDC/MFA per blueprint §22 later.)

Generated files under `packages/contracts/src/` are do-not-edit — change the JSON
Schema in `contracts/` and rerun `pnpm gen:contracts`.
