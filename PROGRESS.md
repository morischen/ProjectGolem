# PROGRESS.md — Living Development Ledger

This is the memory of the loop-engineering framework. Every working session reads
it first and updates it last. See [CLAUDE.md](CLAUDE.md) §1 (pre-session checklist)
and §2 (The Loop) for the protocol.

**Rules**
- An unrecorded loop did not happen. Update this file at the end of every loop.
- Be honest about failures — record the *actual* error, not a paraphrase.
- "Next" is a commitment to the following loop, not a wishlist.
- Convert relative dates to absolute (YYYY-MM-DD).
- Keep entries terse. Detail belongs in code, ADRs (`docs/`), or commit messages.

Legend: ✅ done · 🔄 in progress · ❌ failed/blocked · ⏭️ next

---

## Current state (2026-06-19)

Stage **L0 — Foundations / Methodology Lab** (per [EIP-blueprint-patch.md](EIP-blueprint-patch.md) §23.3).
Phase: **project scaffolding / documentation foundation.** No code yet.

Decisions locked:
- Stack: **polyglot** — Python (FastAPI) for AI/GraphRAG services; TypeScript
  (Fastify gateway + Next.js portal). Shared contracts code-generated.
- Data stores: Neo4j, Qdrant, PostgreSQL, S3-compatible (MinIO in dev).
- This step: **docs only** — no source code, no scaffolding yet.

---

## ✅ Done

- **2026-06-19** — Reworked roadmap into capability-gated model, revised success
  metrics, and authored the gold-benchmark spec → [EIP-blueprint-patch.md](EIP-blueprint-patch.md) (v1.1).
- **2026-06-19** — Established loop-engineering foundation docs:
  [CLAUDE.md](CLAUDE.md) (operating contract + invariants + coding guidelines),
  [ARCHITECTURE.md](ARCHITECTURE.md) (stack, services, data model, repo layout),
  and this ledger.
- **2026-06-19** — Hardened the loop framework: added a **pre-session checklist**
  (CLAUDE.md §1), created **[docs/adr/](docs/adr/)** with a README, template, and
  ADRs 0001 (use ADRs), 0002 (polyglot stack), 0003 (deterministic Trust Engine),
  and added a soft **pre-commit hook** (`scripts/git-hooks/pre-commit`) that warns
  when a commit omits PROGRESS.md. Activated via `core.hooksPath`. Hook tested:
  warns (exit 0) without PROGRESS.md staged, silent with it.
- **2026-06-19** — Built the first code vertical: the **deterministic Trust
  Engine** at [ai-services/trust-engine/](ai-services/trust-engine/). Pydantic
  models (Evidence/Verdict/ScoringWeights/TrustResult), pure §10 weighted scoring
  with verdict mapping, contradiction-as-mass, and single-source (laundering)
  resistance. **14/14 pytest tests pass** (determinism, weights-sum, formula
  fixtures, all six verdicts, Insufficient/Mixed as real outcomes, contradiction
  flips Verified→Mixed). Added root `.gitignore`.
- **2026-06-19** — **Claim Engine vertical** (`ai-services/claim-engine`): first
  consumer of `claim.schema.json`. LLM extraction + claim-type classification via a
  **recorded LLM wrapper** ([ADR-0005](docs/adr/0005-llm-recorded-wrapper.md)):
  `RecordedCall` captures model+prompt+inputs (INV-REPRO); `StubLLMClient` keeps
  tests offline/green; `AnthropicLLMClient` (Claude Opus 4.8, adaptive thinking)
  scaffolded for runtime. LLM never scores (INV-DETERMINISM); output validated
  against the Claim contract. QA green: 11 tests + smoke; wired into the repo gate
  + CI.
- **2026-06-19** — **Portal → live data**: `fetchVerdict` (server-side) calls the
  gateway `POST /v1/score` (`GATEWAY_URL`) and renders the result, with a static
  `sample.ts` fallback when the gateway is unreachable (keeps tests/`next build`
  hermetic). The full path is now demoable: portal → gateway → FastAPI → engine.
  QA green: portal 6 tests (+gateway 5, Python 46).
- **2026-06-19** — **Gateway → Trust Engine wiring**: typed `ScorerClient` +
  `POST /v1/score` proxy route on the Fastify gateway (`TRUST_ENGINE_URL`,
  default :8000). Gateway validates + forwards, never scores (INV-DETERMINISM);
  502 on engine error, 400 on bad body. Mocked-fetch integration tests. QA green:
  gateway 5 tests + portal 3 + Python 46.
- **2026-06-19** — **Trust Engine HTTP surface** (FastAPI, `eip_trust.api`):
  `GET /health` + `POST /v1/score` ({evidence[], historical}) → `TrustResult`.
  Thin transport over the deterministic scorer (still no scoring in the API layer,
  INV-DETERMINISM); `make serve` runs it via uvicorn. TestClient tests (in-process,
  no server). QA green: 46 Python tests + web.
- **2026-06-19** — **Public portal** (Next.js, `web/portal`): read-only
  transparency surface — `VerdictCard` shows the verdict, full confidence
  breakdown, and the *strongest opposing evidence* (FR-008), typed against
  `@eip/contracts` (presentation only, no scoring). vitest + Testing Library
  (3 tests). QA green across both stacks.
- **2026-06-19** — **web/ + infra scaffolding**: pnpm workspace; `@eip/contracts`
  TS types generated from `contracts/` (TS half of ADR-0004, `pnpm gen:contracts`);
  Fastify **api-gateway** (`/health`, `/v1/info`) consuming the generated `Verdict`
  type, with vitest tests; `infra/docker-compose.yml` for Neo4j/Qdrant/Postgres/
  MinIO. QA gate + CI extended to the web workspace. Next.js **portal deferred**.
  QA green: web typecheck + 2 tests + prettier; full `./scripts/qa.sh` passes both
  stacks.
- **2026-06-19** — **Gold-benchmark harness stub** (§28): `eip_trust.benchmark`
  with a `BenchmarkItem` model (strata tags, matched-pair id), a JSON loader, and a
  runner computing verdict accuracy (overall + per difficulty) + a calibration-error
  stub. Seed set of 9 labeled items (all verdicts + a matched framing pair + a
  historical case) doubles as golden fixtures; wired into the QA gate (`make bench`,
  fails if accuracy < 100%). QA green: 41 tests, smoke OK, bench 100%.
- **2026-06-19** — **Trust Engine hardening**: added a pure `freshness_from_age_days`
  helper (exponential decay, no clock — stays deterministic) and claim-type/domain
  weight **profiles** (`weights_for`, `HISTORICAL_WEIGHTS` discounts freshness for
  settled history; each profile versioned). New public exports. QA green: 30 tests,
  ruff/mypy clean, smoke OK.
- **2026-06-19** — **Dev-tooling lane**: added `ruff` + `mypy --strict` (pydantic
  plugin) as dev deps with config; a reusable QA gate (`scripts/qa.sh` →
  per-service `make qa` = lint + typecheck + test + smoke), a runtime smoke check
  (`scripts/smoke.py`), and GitHub Actions CI (`.github/workflows/ci.yml`,
  incl. codegen-drift check). Gate green: ruff/mypy clean, 21 tests, smoke OK.
- **2026-06-19** — **Contracts v0**: authored [contracts/](contracts/) JSON
  Schemas (evidence, verdict, claim) as the source of truth; chose
  datamodel-code-generator ([ADR-0004](docs/adr/0004-contract-codegen-toolchain.md))
  and generated Pydantic models into `eip_trust/_generated/` (do-not-edit, `make
  gen`). Migrated the engine to consume generated shapes via a thin `models.py`
  facade (public API unchanged; `ScoringWeights` moved to `weights.py`). Added
  jsonschema conformance tests. **21/21 pytest tests pass.**

---

## 🔄 In progress

- **Autonomous loop session** (owner directive): after each loop run tests + QA
  (ruff/mypy) + smoke, then commit & push, then continue. Working the Next list.

---

## ❌ Failed / Blocked

- **(RESOLVED 2026-06-19) Env: pip default index was a private JFrog Artifactory.**
  `index-url` in `~/.config/pip/pip.conf` pointed at `*.jfrog.io` (with embedded
  plaintext credentials) and did not serve `pydantic`/`pytest`. **Fixed:**
  `pip config unset global.index-url` — pip now uses public PyPI by default;
  install verified with no override, tests green. (Network egress is still
  sandboxed at the harness level, so installs run via the sandbox-disabled path.)
- **(RESOLVED 2026-06-19) Env: `uv` not installed.** Installed via Homebrew
  (uv 0.11.23). Trust Engine migrated to `uv sync` / `uv run pytest`; `uv.lock`
  committed for reproducible installs. Tests green (14/14) under uv.

---

## ⏭️ Next (proposed — confirm before starting)

In priority order. Each is one loop unless noted.

1. **Claim Engine HTTP + gateway wiring** — expose claim-engine over FastAPI
   (`POST /v1/extract` → `Claim`) and add a gateway route; first claim→evidence→
   verdict path stitched together.
2. **Portal depth** — evidence graph view, contradictions panel, appeal entry;
   accessibility pass.
3. **End-to-end integration test** — optional real round-trip (spin up FastAPI +
   gateway) in CI, complementing the mocked unit tests.

---

## Backlog (not yet scheduled)

- ADRs for open decisions in ARCHITECTURE.md §8 (codegen, canonical record
  ownership, embeddings/chunking, multilingual pipeline, auth provider).
- New blueprint sections flagged earlier but not written: **Legal & Liability**,
  **Platform Threat Model**, and a **Budget revision** (§25) to cover labeler
  compensation, certifications, data licensing, translation, and audits.

---

## Loop log (append-only, newest first)

- **2026-06-19** — Claim Engine loop (autonomous session): new `claim-engine`
  service — recorded LLM wrapper (stub + Anthropic scaffold) + extractor + Claim
  codegen + ADR-0005; added to repo QA gate and CI. Verification: `./scripts/qa.sh`
  → trust-engine 46 + claim-engine 11 + gateway 5 + portal 6, all green.
- **2026-06-19** — Portal→live-data loop: `fetchVerdict` (gateway call + static
  fallback) wired into the page; mocked-fetch tests (live / unreachable / non-2xx).
  Verification: `./scripts/qa.sh` → Python 46 + gateway 5 + portal 6, typecheck/fmt.
- **2026-06-19** — Gateway→engine wiring loop (autonomous session): ScorerClient +
  `/v1/score` proxy + mocked-fetch integration tests (happy/400/502). Verification:
  `./scripts/qa.sh` → Python 46 + gateway 5 + portal 3, typecheck + prettier.
- **2026-06-19** — Trust Engine HTTP surface loop (autonomous session): FastAPI
  `eip_trust.api` (/health, /v1/score) + TestClient tests + `make serve`.
  Verification: `./scripts/qa.sh` → 46 Python tests + web; live POST /v1/score 200.
- **2026-06-19** — Public portal loop (autonomous session): Next.js `web/portal`
  with a typed `VerdictCard` transparency component + Testing Library tests.
  Verification: `./scripts/qa.sh` → Python (41/smoke/bench) + web (gateway 2,
  portal 3, typecheck, prettier).
- **2026-06-19** — web/ + infra scaffolding loop (autonomous session): pnpm
  workspace, `@eip/contracts` TS codegen, Fastify api-gateway (+vitest),
  docker-compose; QA + CI extended to web. Portal deferred. Verification:
  `./scripts/qa.sh` → Python (41 tests/smoke/bench) + web (typecheck/2 tests/fmt).
- **2026-06-19** — Gold-benchmark harness stub loop (autonomous session): item
  model + loader + runner (verdict accuracy + calibration stub) + 9-item seed +
  `make bench`. Verification: `./scripts/qa.sh` → 41 tests, smoke OK, bench 100%.
- **2026-06-19** — Trust Engine hardening loop (autonomous session):
  freshness-from-age helper + versioned weight profiles (default/historical).
  Verification: `./scripts/qa.sh` → 30 tests, ruff/mypy clean, smoke OK.
- **2026-06-19** — Dev-tooling lane loop (autonomous session): ruff + mypy strict
  + reusable QA gate (`scripts/qa.sh`) + smoke + CI. Verification:
  `./scripts/qa.sh` → ruff/format/mypy clean, 21 tests, smoke verdict=Verified.
- **2026-06-19** — Contracts v0 loop: `contracts/` JSON Schemas + ADR-0004 +
  generated Pydantic models (`make gen`) + engine migration to a facade +
  jsonschema conformance tests. Verification: `uv run pytest` → **21 passed**.
  Note: `ruff`/`mypy` referenced but not yet installed → queued as next loop.
- **2026-06-19** — Committed the foundational baseline (docs + framework + Trust
  Engine) as the repo's first commit. Set git identity to moris.chen@gmail.com;
  working directly on `main` per owner directive (CLAUDE.md §8). 14/14 tests green.
- **2026-06-19** — Cleaned up Python toolchain env: removed private JFrog index
  from pip config (now uses public PyPI); installed `uv` (Homebrew); migrated
  Trust Engine to `uv sync`/`uv run` with committed `uv.lock`. Both env blockers
  resolved. Verification: `uv run pytest` → 14 passed.
- **2026-06-19** — Built deterministic Trust Engine vertical
  (`ai-services/trust-engine/`): Pydantic models + pure §10 scoring + verdict
  mapping. Verification: `pytest` **14 passed**. Blockers hit and worked around:
  pip default index (JFrog) lacks deps → used PyPI index + sandbox-disabled
  install; `uv` absent → venv+pip. Recorded under Failed/Blocked. Next: contracts
  v0, then migrate models to generated types.

- **2026-06-19** — Added pre-session checklist, `docs/adr/` (README + template +
  ADRs 0001–0003), and soft pre-commit PROGRESS.md reminder hook. Renumbered
  CLAUDE.md sections (checklist is now §1, Loop §2). Verification: hook tested both
  branches (warn / silent), both exit 0. Next: repo scaffolding (item 1), pending
  go-ahead.
- **2026-06-19** — Created CLAUDE.md, ARCHITECTURE.md, PROGRESS.md. Stack +
  scope decisions captured. Verification: docs only, nothing to lint/test.
  Next: repo scaffolding (item 1 above), pending user go-ahead.
