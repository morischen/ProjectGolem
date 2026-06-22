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
- **2026-06-21** — **#3 hardening: error handling + calibration harness**.
  (a) `eip-llm`: `LLMError` for refusals/empty completions; configurable `timeout` +
  `max_retries` on `OpenRouterLLMClient` (SDK retries 429/5xx/timeouts), wired via
  `OPENROUTER_TIMEOUT`/`OPENROUTER_MAX_RETRIES`. Claim/evidence APIs map `LLMError`
  → **502** (clean, not opaque 500). (b) Calibration harness in `e2e`
  (`calibration.py`): runs the LLM over labeled claims (classify → score → compare),
  reporting relation + verdict accuracy; hermetic test (stub) + guarded live test.
  **Live-verified** against Opus 4.8 via OpenRouter. Gate green: eip-llm 12, claim 16
  (+1 skip), evidence 30 (+1 skip), e2e 6 (+1 skip).
- **2026-06-21** — **Structured outputs + guarded live tests** (Backlog #3): added a
  `response_format` passthrough (OpenAI-compatible JSON mode, `JSON_OBJECT_RESPONSE_FORMAT`)
  and a tolerant `extract_json` parser (handles fences/prose/embedded JSON) to
  `eip-llm`; claim-engine + evidence-engine now request JSON mode and parse with it.
  Added guarded live integration tests (`test_live.py`, skip without an LLM key) for
  both engines. **Live-verified**: both passed against `anthropic/claude-opus-4.8`
  via OpenRouter. Hermetic gate stays green (live tests skip): eip-llm 11, claim 15
  (+1 skipped), evidence 29 (+1 skipped).
- **2026-06-21** — **OpenRouter live-verified** + `max_tokens` cap: confirmed the
  real path works (`OpenRouterLLMClient` → `anthropic/claude-opus-4.8` → "OK").
  Added `max_tokens` to `OpenRouterLLMClient` (default 1024; `OPENROUTER_MAX_TOKENS`
  env) — without it OpenRouter assumes the model max and 402s on low-credit keys.
- **2026-06-21** — **Dev `.env` credentials**: added committed `.env.example`
  (documents every var — OpenRouter/Anthropic keys, gateway auth, data-store DSNs,
  service URLs) and a gitignored local `.env`; `scripts/dev.sh` now loads `.env`
  (`set -a; . .env`). Data-store vars are commented by default (Postgres connects at
  startup); `EIP_API_KEYS` left unset so the portal stays keyless in dev.
- **2026-06-21** — **OpenRouter multi-model LLM** ([ADR-0009](docs/adr/0009-openrouter-multi-model.md)):
  added `OpenRouterLLMClient` to `eip-llm` (OpenAI-compatible; one key, many models;
  `model_id` = OpenRouter slug) + `build_llm_from_env()` selector (OpenRouter when
  `OPENROUTER_API_KEY` set, else Anthropic). claim/evidence engines now default to it.
  Hermetic (injectable client, fake in tests) — `eip-llm` is now a tested lib (5
  tests) wired into the gate + CI. This is the chosen path to unblock real LLM use:
  set `OPENROUTER_API_KEY` (+ `OPENROUTER_MODEL`) and the pipeline runs live.
- **2026-06-21** — **Gateway → Trust Engine field passthrough**: the gateway's
  `/v1/score` now forwards `claim_id`, `independence`, and `event_time` to the Trust
  Engine, so verdict persistence (ADR-0008) and the independence override (ADR-0007)
  work through the gateway, not just the Python API directly. Test asserts the
  forwarded request body. gateway 20.
- **2026-06-20** — **Gateway auth + rate limiting** (Backlog #4): API-key auth with
  scopes/RBAC (`requireScope`; `EIP_API_KEYS` env, `x-api-key` header; 401/403) and an
  injectable-clock in-memory fixed-window rate limiter (`createRateLimiter`/
  `rateLimitHook`; 429 + `x-ratelimit-remaining`). The three `/v1/*` proxy routes are
  protected (scope `write`); health/info stay public; no keys → dev/open mode. 8 new
  vitest tests (gateway 19). (OIDC/MFA per §22 noted as the next cut.)
- **2026-06-20** — **Governance docs** (blueprint patch → v1.2): wrote the three
  sections flagged in the original review — **§25 Budget (revised)** with the omitted
  line items (data licensing, legal/insurance, certifications, reviewer/labeler pay,
  translation, audits; total \$2.2M–4.3M), **§29 Legal & Liability** (evidence-not-
  guilt stance, defamation posture, correction/retraction via the bitemporal store,
  right-of-reply/appeals, source protection, privacy↔immutability resolution,
  insurance), **§30 Platform Threat Model** (threats turned inward, each mapped to a
  control with ✅/◐/○ status — the implemented ADRs 0003/0005/0007/0008 are the
  primary mitigations). Docs-only; code gate unaffected.
- **2026-06-19** — **Persistence Q3 — persist verdicts + history API**: Trust Engine
  `POST /v1/score` now persists an append-only versioned snapshot when a `claim_id`
  is supplied and a store is configured (eip-persistence path dep; `knowledge_time`
  stamped at the HTTP boundary, store stays pure). New read endpoints
  `GET /v1/claims/{id}/verdicts` (history) and `/verdict` (latest). The append-only
  history is the audit / calibration-ledger foundation. trust-engine 54.
  **Initiative #2 (persistence & bitemporal verdicts) complete.**
- **2026-06-19** — **Persistence Q2 — SQL adapter**: `SqlVerdictStore` (SQLAlchemy
  Core) implements `VerdictStore` over the same code on SQLite and Postgres;
  append-only with per-claim version computed in a transaction + unique constraint.
  Tested hermetically against in-memory SQLite (real SQL round-trip, no Docker);
  `make_postgres_store` + docker-compose docs for production. eip-persistence: 13 tests.
- **2026-06-19** — **Persistence Q1 — bitemporal verdict store**: new shared lib
  [eip-persistence](ai-services/libs/eip-persistence/) ([ADR-0008](docs/adr/0008-bitemporal-verdict-store.md))
  — append-only, versioned `VerdictRecord`s (frozen) behind a `VerdictStore` protocol
  with `InMemoryVerdictStore`. Two time axes (knowledge/event), caller-supplied
  timestamps (deterministic), and `as_of(t)` answers "what did we conclude on date X"
  (INV-TEMPORAL; Principle 5). 8 tests; wired into the gate + CI.
- **2026-06-19** — **Independence → Trust Engine wiring**: `score_claim` now accepts
  an optional `independence` override (clamped) that replaces the count-based
  heuristic with the graph-derived `independence_ratio` (ADR-0007); exposed on the
  Trust Engine's `POST /v1/score` (`independence` field). End-to-end test proves
  laundered corroboration (3 sources → 1 origin) flips **Verified → Likely True**.
  trust-engine 49, e2e 4.
- **2026-06-19** — **Real retrieval P3 — composite + env-wired API**:
  `CompositeRetriever` (merge + dedup by id, keep highest quality) +
  `build_retriever_from_env` (assembles Qdrant/Neo4j backends from `QDRANT_URL`/
  `NEO4J_URI`). Evidence Engine `/v1/gather` now retrieves server-side when no
  candidates are supplied (injected/env retriever), else uses request candidates.
  docker-compose validation docs added. evidence-engine: 29 tests. **Initiative #1
  (real retrieval) complete.**
- **2026-06-19** — **Real retrieval P2 — graph retriever + independence analysis**:
  `GraphStore` seam + `Neo4jGraphStore` adapter (`make_neo4j_store`; `neo4j` dep) +
  `GraphRetriever` (drop-in `Retriever`). Plus the differentiator
  ([ADR-0007](docs/adr/0007-independence-citation-laundering.md)):
  `assess_independence` groups sources into provenance clusters (weakly-connected
  components of the citation graph) so shared-origin / citation-cycle "corroboration"
  is detected — `independence_ratio` < 1 means laundered. Pure + hermetic.
  evidence-engine: 25 tests.
- **2026-06-19** — **Real retrieval P1 — semantic/vector retriever**: added
  retrieval seams ([ADR-0006](docs/adr/0006-retrieval-seams.md)) — `Embedder` +
  `VectorStore` protocols with `StubEmbedder` and a `QdrantVectorStore` adapter
  (`make_qdrant_store` factory; `qdrant-client` dep). `SemanticRetriever` embeds the
  claim → vector search → `Candidate`s (similarity → quality), and is a drop-in
  `Retriever` for `gather()`. Hermetic tests with a fake vector store (no live DB).
  evidence-engine: 17 tests.
- **2026-06-19** — **Dev ergonomics**: `scripts/dev.sh` (+ root `pnpm dev`) boots
  the whole stack on fixed ports (trust :8000, claim :8001, evidence :8002, gateway
  :4000, portal :3000) with Ctrl-C cleanup; portal page set to `force-dynamic` so
  production also fetches live. Verified end-to-end: gateway `/health` 200, live
  `POST /v1/score` → Verified, portal banner flips to "Live verdict from gateway"
  (Likely True). Also whitelisted esbuild's pnpm build script (warning gone).
- **2026-06-19** — **End-to-end integration test** (`ai-services/e2e`): a
  non-package uv project path-depending on all three engines; drives
  **claim → evidence → trust** in one process with stubs, exchanging `Evidence` as
  JSON (the real HTTP boundary). Proves the independently-generated contracts line
  up (Verified + Mixed paths; cross-engine `EvidenceRelation` parity). Added to the
  repo QA gate + CI. 3 tests green.
- **2026-06-19** — **Portal depth**: added a `ContradictionsPanel` (opposing
  evidence surfaced first-class, with count + empty state) and an `AppealEntry`
  affordance (states appeals are logged publicly), both with accessible
  `region`/`button` roles and vitest tests. Wired into the page. Portal: 10 tests.
- **2026-06-19** — **Evidence Engine HTTP + gateway wiring**: FastAPI
  `eip_evidence.api` (`/health`, `POST /v1/gather` {claim_text, candidates} →
  `Evidence[]`) with injectable LLM (`make serve`, port 8002). Gateway gains a typed
  `EvidenceClient` + `POST /v1/gather` proxy (`EVIDENCE_ENGINE_URL`, default :8002).
  Gateway now fronts all three engines (`/v1/extract`, `/v1/gather`, `/v1/score`).
  QA green: evidence 12 + gateway 11.
- **2026-06-19** — **Shared `eip-llm` lib**: extracted the recorded LLM wrapper
  (`RecordedCall`/`LLMClient`/`StubLLMClient`/`AnthropicLLMClient`) into
  [ai-services/libs/eip-llm](ai-services/libs/eip-llm/) (PEP 561 `py.typed`).
  claim-engine and evidence-engine now depend on it via a uv path dependency and
  deleted their local copies. Pays down the flagged duplication. QA green across
  all services; `StubLLMClient` unified (sequential outputs).
- **2026-06-19** — **Evidence Retrieval Engine vertical** (`ai-services/evidence-engine`):
  the pipeline's middle — `gather()` retrieves candidates (`Retriever` seam,
  `StubRetriever` for tests) and the LLM classifies each one's relation
  (Supports/Contradicts/Neutral/Inconclusive) via the recorded wrapper; quality/
  freshness/tier come from retrieval metadata, not the LLM. Emits contract-valid
  `Evidence` ready for the Trust Engine. LLM never scores (INV-DETERMINISM). QA
  green: 8 tests + smoke; wired into the repo gate + CI. (LLM wrapper duplicated
  from claim-engine — flagged to extract into a shared lib.)
- **2026-06-19** — **Claim Engine HTTP + gateway wiring**: FastAPI `eip_claim.api`
  (`/health`, `POST /v1/extract` → `Claim`) with an injectable LLM client (stub in
  tests, Anthropic at runtime; `make serve`, port 8001). Gateway gains a typed
  `ClaimClient` + `POST /v1/extract` proxy (`CLAIM_ENGINE_URL`, default :8001),
  mocked-fetch tests. QA green: claim-engine 15 + gateway 8.
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

- _Nothing in flight._ **The entire scheduled backlog is drained** (admin portal
  A1–A4, end-to-end assessment, graph independence, calibration ledger, expanded
  benchmark, rate-limit seam, offline embedder + graph seeding, multi-approver
  config control, public claim submission, ADRs). Only infra-blocked items remain —
  see **Backlog → Deferred**. Pick one up when the supporting infrastructure exists.

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

✅ **The full roadmap and backlog are implemented.** Nothing is scheduled. The only
remaining work is the infra-blocked **Deferred** list under Backlog — each has a
tested seam/adapter awaiting the live service (OIDC provider, Redis, hosted embedding
model, running Neo4j/Qdrant, Postgres-backed KeyStore) or external data (larger §28
corpus). Plus the standing operational task: **rotate the leaked OpenRouter dev key**.

---

## Backlog (not yet scheduled)

Larger initiatives, not single mechanical loops — each needs its own scoping:

**The backlog is drained** — every scheduled initiative is implemented and green.
What remains is genuinely blocked on external infrastructure (see "Deferred" below);
the code seams/adapters for those are in place and tested.

- ✅ **Real retrieval backends — DONE** (P1 Qdrant semantic, P2 Neo4j graph +
  independence/citation-laundering, P3 composite + env-wired API + docker-compose
  docs). Follow-ups all DONE: offline `HashingEmbedder` behind the Embedder seam
  (a real lexical embedder; hosted multilingual model is the deferred step),
  `graph_schema.py` + `scripts/seed_graph.py` (Neo4j constraints/indexes), and
  `independence_ratio` threaded end to end through the gateway (`/v1/assess` →
  `/v1/independence` → score).
- ✅ **Persistence & bitemporal verdicts — DONE** (store + SQL adapter +
  persist-in-pipeline + history API). Follow-ups DONE: full append-only audit log
  (`AuditStore`, A2) and gateway `claim_id` passthrough to `/v1/score`.
- ✅ **Real LLM enablement — DONE** (OpenRouter, ADR-0009): recorded client + env
  selector + structured outputs + LLMError/timeout/retry handling + calibration
  harness, live-verified vs Opus 4.8. The gold seed grew 9 → 21 cases; a *larger
  real-world labeled corpus* for full §28 ECE/bias gates is deferred (data sourcing).
- ✅ **AuthN/Z + rate limiting — DONE**: API-key scopes/RBAC + managed `KeyStore`
  (hashed, A4) + a pluggable `RateLimitStore` seam (in-memory default; Redis adapter
  deferred to infra). OIDC/MFA recorded as [ADR-0013] and deferred (needs a provider).
- ✅ **Admin portal — DONE** (A1–A4). Follow-ups DONE: persistent calibration ledger
  (§28.12, `CalibrationStore` + Dashboard trend) and multi-approver change control
  (config proposals + approvals). DB-backed KeyStore deferred (infra).
- ✅ **End-to-end claim assessment — DONE** (`POST /v1/assess` + admin Assess tab +
  graph-independence override). ✅ **Public claim-submission surface — DONE**
  (`/v1/claims/submit` → `claim_intake` review item; portal `ClaimSubmit`).
- ✅ **ADRs for open decisions — DONE** (ADR-0010 Accepted; 0011/0012/0013 Proposed).
- ✅ **Blueprint governance sections — DONE** (v1.2): Legal & Liability (§29),
  Platform Threat Model (§30), Budget revision (§25).

### Deferred — blocked on external infrastructure (seams in place, live wiring pending)
These need a running service / hosted model / data we can't stand up in the
hermetic sandbox; each has a tested code seam or adapter ready to plug in:
- **OIDC/MFA provider** (ADR-0013) — gateway validates tokens → existing scope model;
  needs a provider (Auth0/Keycloak/Cognito-class).
- **Redis (or shared) rate-limit store** — implement `RateLimitStore.hit()` with
  `INCR`+`PEXPIRE`; the seam + in-memory default already ship.
- **Hosted multilingual embedding model** (ADR-0011) — implement the `Embedder`
  protocol; the offline `HashingEmbedder` is the working default meanwhile.
- **Live Neo4j/Qdrant projection + seeding** — `scripts/seed_graph.py` and the
  retriever adapters are ready; needs the running DBs (infra/docker-compose) and a
  canonical→projection sync job.
- **DB-backed KeyStore** — persist the gateway `KeyStore` to Postgres for multi-replica.
- **Larger labeled §28 calibration corpus** — to run ECE/bias gates at real scale.
- **Rotate the leaked OpenRouter dev key** (operational, not code) — still outstanding.

---

## Loop log (append-only, newest first)

- **2026-06-21** — Public claim-submission loop: Trust Engine `POST /v1/claim-intake`
  queues a public claim proposal as a `claim_intake` review item (audited, triaged
  before assessment); gateway public rate-limited `POST /v1/claims/submit`; portal
  `ClaimSubmit` form (lib/gateway.submitClaim) alongside AppealEntry. Assessment stays
  authenticated — the public path only enqueues. Verification: hermetic
  `./scripts/qa.sh` green (trust-engine 88, gateway 57, portal 14); portal build OK.
- **2026-06-21** — Multi-approver config change control loop (governance §20): added
  `proposals.py` (ConfigProposal + InMemoryProposalStore with separation-of-duties
  rules) and Trust Engine endpoints `POST /v1/config/proposals` (validates weights
  up front), `GET /v1/config/proposals`, `POST /v1/config/proposals/{id}/approve`.
  A change applies only after `CONFIG_REQUIRED_APPROVALS` (default 2) **distinct**
  approvers — none the proposer — sign off; applying writes a new audited config
  version. Direct `POST /v1/config` still works (single-actor) via a shared
  `_apply_config` helper. Verification: hermetic `make qa` green (trust-engine 86).
  Gateway/admin-UI exposure is a thin follow-up.
- **2026-06-21** — Local embedder + graph seeding loop (ADR-0011/0010): added
  `HashingEmbedder` — a real (if simple) offline lexical embedder (hashed
  bag-of-words + TF, L2-normalized, Unicode-tokenized for AR/HE/EN) behind the
  ADR-0006 `Embedder` seam; `build_retriever_from_env` now uses it (EMBED_DIM-tunable)
  instead of the wiring stub. Added `graph_schema.py` (idempotent Neo4j constraints +
  indexes) + `apply_schema` + `scripts/seed_graph.py` (env-driven, `--dry-run`).
  Verification: hermetic `make qa` green (evidence-engine 40; similar-text cosine >
  dissimilar; seed dry-run prints 6 statements). A hosted multilingual model + live
  Neo4j execution remain deferred (infra).
- **2026-06-21** — Rate-limit store seam loop (blueprint §22): refactored the gateway
  limiter behind a `RateLimitStore` interface (one `hit()` method) with an
  `InMemoryRateLimitStore` default; `createRateLimiter`/`rateLimitHook` accept an
  injected store so a Redis adapter can share counters across replicas. Proven with a
  shared-store-across-two-limiters test. Verification: `./scripts/qa.sh` green
  (gateway 56). The live Redis adapter itself is deferred (needs infra).
- **2026-06-21** — Benchmark seed expansion loop (§28 calibration): grew the gold
  seed set from 9 → 21 labeled cases (more verdicts/difficulties/tiers — tier-2/3/4
  sources, mid-quality Likely True/False, even/leaning Mixed, faint/zero-mass
  Insufficient). Each verified golden (engine reproduces the label). Verification:
  hermetic `make qa` green (trust-engine 80; verdict accuracy 100%; ECE 0.236).
- **2026-06-21** — Calibration ledger gateway+UI loop: gateway `admin`-scoped
  `GET /admin/calibration` + `POST /admin/calibration/run`; admin Dashboard lists
  recorded runs with a "Record a run" button. Verification: `./scripts/qa.sh` green
  (gateway 55, admin 30).
- **2026-06-21** — Calibration ledger backend loop: `eip-persistence`
  `CalibrationStore` (append-only run history, in-memory + SQL) + `CalibrationRunRecord`;
  Trust Engine `POST /v1/calibration/runs` (re-runs the gold benchmark and records a
  snapshot) + `GET /v1/calibration/runs` (newest first). Realizes the §28.12
  calibration ledger. Verification: hermetic `make qa` green (persistence 64,
  trust-engine 80; mypy/bench OK).
- **2026-06-21** — ADRs for open decisions loop: recorded the four remaining
  ARCHITECTURE.md §8 open decisions as ADR-0010 (canonical record ownership: Postgres
  canonical + Neo4j projection — Accepted), ADR-0011 (embeddings + chunking —
  Proposed), ADR-0012 (multilingual pipeline — Proposed), ADR-0013 (auth: API keys
  now, OIDC later — Proposed); updated the ADR index and §8 to link them. Docs-only;
  verification: ADR files exist and links resolve.
- **2026-06-21** — Independence IND2 (thread through assess) loop: `EvidenceClient`
  gains `independence()`; gateway `/v1/assess` accepts optional `citations` —
  derives `independence_ratio` from the gathered sources via the evidence engine and
  passes it to scoring as the ADR-0007 override (omitted → Trust Engine heuristic).
  Admin `AssessClaim` gains a citations input (validated). Completes the
  graph-independence-through-assess follow-up. Verification: hermetic
  `./scripts/qa.sh` green (gateway 54, admin 29; all suites).
- **2026-06-21** — Independence IND1 (evidence endpoint) loop: evidence-engine
  `POST /v1/independence` exposes `assess_independence` (source_ids + citations →
  distinct/independent-group counts + `independence_ratio` + groups), so
  citation-laundering can be measured over the HTTP boundary (ADR-0007). Pure, no
  LLM/scoring. Verification: hermetic `make qa` green (33 passed; mypy clean).
- **2026-06-21** — Assess pipeline AS2 (admin Assess tool) loop: admin app gains an
  `AssessClaim` component (new Assess tab) — submit claim text + claim id + optional
  evidence candidates (JSON), call `POST /v1/assess`, and render the verdict, score,
  config version, confidence breakdown, and classified evidence. `adminApi.assess`
  added; invalid-candidates JSON is caught client-side. **Completes the end-to-end
  assessment initiative.** Verification: hermetic `./scripts/qa.sh` green (admin 28
  tests; all suites); `pnpm build` (admin) succeeds.
- **2026-06-21** — Assess pipeline AS1 (gateway orchestration) loop: new
  `POST /v1/assess` (write-scoped) orchestrates claim extract → evidence gather →
  score (+ persist) in one call and returns `{claim, evidence, result}`. Gateway only
  orchestrates (INV-DETERMINISM); the verdict is produced + persisted by the Trust
  Engine. 400 on missing text/claim_id, 502 on any pipeline-stage failure.
  Verification: hermetic `./scripts/qa.sh` green (gateway 52 tests; all suites).
- **2026-06-21** — Admin portal A4.4 (access-management UI) loop: admin app gains an
  `AccessManagement` component (new Access tab) — list keys by prefix (never the
  secret), create a key (label + scope checkboxes; plaintext shown once), and revoke
  (soft-disable), via `listKeys`/`createKey`/`disableKey` → `/admin/keys`.
  **Completes A4 and the full A1–A4 admin portal.** Verification: hermetic
  `./scripts/qa.sh` green (admin 25 tests; all suites); `pnpm build` (admin) succeeds.
- **2026-06-21** — Admin portal A4.3 (access-management backend) loop: Trust Engine
  `POST /v1/audit` (central audit sink). Gateway gains a `KeyStore` — API keys held
  only as SHA-256 hashes, seeded from `EIP_API_KEYS` (backward compatible), with
  `create` (plaintext shown once), `authenticate`, `list` (metadata only), and soft
  `disable`. `requireScope` now resolves through the store. New `admin`-scoped
  `GET/POST /admin/keys` + `POST /admin/keys/:id/disable`, mirrored to the audit log
  (best-effort). Verification: hermetic `./scripts/qa.sh` green (trust-engine 77,
  gateway 48; all suites; mypy/bench OK).
- **2026-06-21** — Admin portal A4.2 (dashboard) loop: admin app gains a `Dashboard`
  component (now the default tab) showing gold-benchmark verdict accuracy +
  calibration error + by-difficulty, review-queue health (open/resolved/by-kind), and
  claims count, via `getMetrics` → `/admin/metrics`. Verification: hermetic
  `./scripts/qa.sh` green (admin 22 tests; all suites); `pnpm build` (admin) succeeds.
- **2026-06-21** — Admin portal A4.1 (metrics endpoint) loop: new Trust Engine
  `metrics` module + `GET /v1/metrics` — gold-benchmark verdict accuracy +
  calibration error + by-difficulty, review-queue health (open/resolved/by-kind),
  and claims count; gateway `admin`-scoped `GET /admin/metrics`. Pure read (re-runs
  the deterministic engine over the labeled seed). Verification: hermetic
  `./scripts/qa.sh` green (trust-engine 76, gateway 40; all suites; mypy/bench OK).
- **2026-06-21** — Admin portal A3.4 (review/appeals UI) loop: admin app gains a
  `ReviewQueue` component (modes: review queue / appeals) with a resolve panel
  (upheld/dismissed/**override** → verdict picker, reviewer + note) wired to
  `/admin/review/:id/resolve`; new Review + Appeals tabs in `page.tsx`. Public portal
  `AppealEntry` is now a real form (type + details) posting to the gateway's public
  `/v1/appeals` via `lib/gateway.submitAppeal`, with success/error states.
  Verification: hermetic `./scripts/qa.sh` green (admin 19, portal 11; all suites);
  `pnpm build` (admin + portal) succeeds. **A3 done.**
- **2026-06-21** — Admin portal A3.3 (gateway review/appeals) loop: extended
  `AdminClient` (listReview/getReview/resolveReview/listAppeals/submitAppeal) and
  added `admin`-scoped `GET /admin/review`, `GET /admin/review/:id`,
  `POST /admin/review/:id/resolve` (forwards 404/409/422), `GET /admin/appeals`, plus
  a **public** rate-limited `POST /v1/appeals` (new `publicLimited()` preHandler —
  rate-limit without an API key). Verification: hermetic `./scripts/qa.sh` green
  (gateway 38 tests; all suites).
- **2026-06-21** — Admin portal A3.2 (Trust Engine review/appeals) loop: wired
  `ReviewStore` into the API. `/v1/score` now auto-enqueues escalations
  (evidence_conflict for Mixed, low_confidence for <0.70), deduped to one open item
  per claim. New endpoints: `GET /v1/review` (status filter), `GET /v1/review/{id}`,
  `POST /v1/review/{id}/resolve` (upheld/dismissed/override — override appends a new
  `human-override` verdict version attributed to the reviewer + audit, realizing
  INV-OVERRIDE), `POST /v1/appeals` + `GET /v1/appeals` (appeals logged in audit).
  Verification: hermetic `make qa` green (73 tests; mypy clean; benchmark OK).
- **2026-06-21** — Admin portal A3.1 (data layer) loop: added `ReviewStore`
  (human-review queue: items of kind low_confidence/evidence_conflict/appeal,
  open→resolved) + `ReviewRecord` model to `eip-persistence`, with in-memory + SQL
  adapters. Review items are operational state (mutable status) — distinct from the
  append-only verdict/config/audit stores; the durable trail of a resolution lives
  in those. Verification: hermetic `make qa` green (54 tests incl. SQLite parity;
  mypy clean across 7 source files).
- **2026-06-21** — Admin portal A2.4 (admin Config page) loop: extended the admin
  app's `adminApi` (getConfig/configHistory/listAudit/updateConfig with typed
  `ConfigRecord`/`ConfigView`/`AuditEntry`) and added a `ConfigEditor` component —
  view active weights/tier-reliability/thresholds, edit with **live sum-to-1
  validation** (save disabled until valid + actor present), profile switch
  (default/historical), version history, and 422 surfacing; tab nav (Claims/Config/
  Sign out) in `page.tsx`. Verification: hermetic `./scripts/qa.sh` green (admin 15
  tests; all suites); `pnpm build` (admin) succeeds. **A2 done.**
- **2026-06-21** — Admin portal A2.3 (gateway config proxies) loop: extended
  `AdminClient` (getConfig/configHistory/updateConfig/listAudit) and added
  `admin`-scoped routes `GET /admin/config`, `GET /admin/config/:profile/history`,
  `POST /admin/config` (forwards the engine's 200/422 verbatim so sum-to-1
  rejections reach the UI), `GET /admin/audit`. Verification: hermetic
  `./scripts/qa.sh` green (gateway 31 tests; all suites).
- **2026-06-21** — Admin portal A2.2 (Trust Engine config) loop: new
  `config_service` (ScoringWeights ↔ ConfigStore: seed, serialize, resolve active,
  version labels) + endpoints `GET /v1/config`, `GET /v1/config/{profile}/history`,
  `POST /v1/config` (creates a new version; sum-to-1/range violations → 422; writes
  an audit entry with before/after), `GET /v1/audit`. The `/v1/score` path now reads
  the active config version and records its label as `weights_version`. Config/audit
  default to in-memory so the surface works without Postgres. Verification: hermetic
  `make qa` green (63 tests; mypy clean; benchmark OK).
- **2026-06-21** — Admin portal A2.1 (data layer) loop: added `ConfigStore`
  (versioned, per-profile, append-only) + `AuditStore` (append-only action log) to
  `eip-persistence`, each with in-memory + SQL adapters; new `ConfigRecord`/
  `AuditRecord` models. Stores are schema-agnostic (payload dicts) so the lib stays
  dependency-light. Verification: hermetic `make qa` green (40 tests incl. SQLite
  parity; mypy clean across 6 source files).
- **2026-06-21** — Admin portal A1.2 (frontend) loop: new `web/admin` Next.js app
  (`@eip/admin`) — API-key login (`admin` scope) + read-only claims list +
  per-claim verdict-history drill-down, calling the gateway `/admin/*` proxies via
  `lib/adminApi`. Wired into the pnpm workspace (`web/*` glob → auto CI/QA), dev.sh
  (`:3001`, points at gateway `:4000`), and `.prettierignore` (Next-managed files).
  Verification: hermetic `./scripts/qa.sh` green (admin 8 tests, portal 10, gateway
  26, all suites); `pnpm build` (admin) succeeds (4 static routes). **A1 done.**
- **2026-06-21** — Admin portal A1.1 (backend) loop: `VerdictStore.list_claims()`
  (in-memory + SQL, latest-per-claim, paginated) + Trust Engine `GET /v1/claims` +
  gateway `admin`-scoped `/admin/claims[...]` proxies (new `AdminClient`). Also let
  Next.js own `web/portal/tsconfig.json`/`next-env.d.ts` via `.prettierignore`
  (stops the per-loop revert dance). Verification: hermetic `./scripts/qa.sh` green
  (persistence 16, trust 57, gateway 26, all suites; mypy clean).
- **2026-06-21** — #3 hardening loop: LLMError + timeout/retries (eip-llm) + 502
  mapping (claim/evidence APIs) + calibration harness (e2e). Verification: hermetic
  `./scripts/qa.sh` green; live calibration + engine live tests PASS with the key.
- **2026-06-21** — Structured-outputs + live-tests loop: response_format JSON mode +
  extract_json in eip-llm; engines use them; guarded live tests (skip without key).
  Verification: hermetic `./scripts/qa.sh` green (live skipped); live tests PASS with
  the key (claim + evidence vs Opus 4.8 via OpenRouter).
- **2026-06-21** — OpenRouter live-verify + max_tokens cap loop: confirmed real call;
  capped OpenRouter max_tokens (default 1024).
- **2026-06-21** — Dev .env loop: `.env.example` template + gitignored `.env` +
  dev.sh auto-load. Verification: dev.sh `bash -n` OK; `.env` sources correctly;
  `git check-ignore .env` confirms it won't be committed.
- **2026-06-21** — OpenRouter multi-model loop: OpenRouterLLMClient +
  build_llm_from_env selector in eip-llm (now a tested lib); engines default to it.
  Verification: `./scripts/qa.sh` → eip-llm 5, all services green.
- **2026-06-21** — Gateway field-passthrough loop: forward claim_id/independence/
  event_time to /v1/score. Verification: `./scripts/qa.sh` → gateway 20, all green.
- **2026-06-20** — Gateway auth + rate-limit loop: API-key scopes + fixed-window
  limiter on `/v1/*`. Verification: `./scripts/qa.sh` → gateway 19, all services green.
- **2026-06-20** — Governance-docs loop: blueprint patch → v1.2 (§25 Budget revised,
  §29 Legal & Liability, §30 Platform Threat Model). Docs-only; no code changes.
- **2026-06-19** — Persistence Q3 loop: Trust Engine persists verdicts (claim_id +
  store) + history/latest endpoints. Initiative #2 complete. Verification:
  `./scripts/qa.sh` → trust 54, eip-persistence 13, all services green.
- **2026-06-19** — Persistence Q2 loop: SqlVerdictStore (SQLAlchemy) tested on
  in-memory SQLite + make_postgres_store + docs. Verification: `./scripts/qa.sh` →
  eip-persistence 13, all services green.
- **2026-06-19** — Persistence Q1 loop: bitemporal verdict store (eip-persistence,
  ADR-0008) — append-only/versioned, `as_of` queries. Verification: `./scripts/qa.sh`
  → eip-persistence 8, all services green.
- **2026-06-19** — Independence→Trust wiring loop: `score_claim(independence=...)`
  override + `/v1/score` field + cross-engine e2e (laundering flips Verified→Likely
  True). Verification: `./scripts/qa.sh` → trust 49, e2e 4, all green.
- **2026-06-19** — Real retrieval P3 loop: CompositeRetriever + env-wired
  `/v1/gather` + docker-compose docs. Initiative #1 complete. Verification:
  `./scripts/qa.sh` → evidence-engine 29, all services green.
- **2026-06-19** — Real retrieval P2 loop: Neo4j graph retriever + independence
  analysis (ADR-0007). Verification: `./scripts/qa.sh` → evidence-engine 25, all green.
- **2026-06-19** — Real retrieval P1 loop: retrieval seams + SemanticRetriever +
  Qdrant adapter (hermetic, fake store). Verification: `./scripts/qa.sh` →
  evidence-engine 17, all services green.
- **2026-06-19** — Dev-ergonomics: `scripts/dev.sh` / `pnpm dev` one-command stack
  runner + portal `force-dynamic`. Verified live path (gateway→trust-engine→portal)
  with real servers. `./scripts/qa.sh` green.
- **2026-06-19** — End-to-end integration test loop (autonomous session): new
  `ai-services/e2e` cross-engine pipeline test (claim→evidence→trust via JSON);
  added to gate + CI. **This drained the queued Next list (Loops A–O).**
  Verification: `./scripts/qa.sh` → trust 46 + claim 15 + evidence 12 + e2e 3 +
  gateway 11 + portal 10, all green.
- **2026-06-19** — Portal depth loop (autonomous session): ContradictionsPanel +
  AppealEntry components with accessibility roles + vitest tests; wired into page.
  Verification: `./scripts/qa.sh` → portal 10, all services green.
- **2026-06-19** — Evidence Engine HTTP + gateway wiring loop (autonomous session):
  FastAPI `/v1/gather` (DI'd LLM) + gateway `EvidenceClient`/proxy + mocked tests.
  Verification: `./scripts/qa.sh` → trust 46 + claim 15 + evidence 12 + gateway 11
  + portal 6.
- **2026-06-19** — Shared eip-llm lib loop (autonomous session): extracted the
  recorded LLM wrapper into `libs/eip-llm`; both engines migrated via uv path dep,
  local copies deleted. Verification: `./scripts/qa.sh` → trust 46 + claim 15 +
  evidence 8 + gateway 8 + portal 6, all green.
- **2026-06-19** — Evidence Retrieval Engine loop (autonomous session): new
  `evidence-engine` — retriever seam + LLM relation classification → contract-valid
  Evidence; added to repo QA gate + CI. Verification: `./scripts/qa.sh` → trust 46
  + claim 15 + evidence 8 + gateway 8 + portal 6.
- **2026-06-19** — Claim Engine HTTP + gateway wiring loop (autonomous session):
  FastAPI `/v1/extract` (DI'd LLM) + gateway `ClaimClient`/proxy + mocked tests.
  Verification: `./scripts/qa.sh` → trust 46 + claim 15 + gateway 8 + portal 6.
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
