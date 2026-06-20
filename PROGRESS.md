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

---

## 🔄 In progress

- _Nothing in flight._

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

1. **Contracts v0** — author `claim.schema.json`, `evidence.schema.json`,
   `verdict.schema.json` in `contracts/`, pick the codegen toolchain, and generate
   Pydantic + TS types. Then migrate the Trust Engine's hand-authored models to the
   generated ones. (Resolves an ADR in ARCHITECTURE.md §8.)
2. **Trust Engine hardening** — add `ruff` + `mypy --strict` config and a CI lane;
   add calibration/golden-fixture tests tied to the gold benchmark (§28); consider
   freshness-from-dates and domain/claim-type-aware weights (blueprint §10/§23).
3. **Gold-benchmark harness stub** — schema + loader for benchmark items
   (spec §28) so L0 gates (G0.x) become measurable early; wire ECE against the
   Trust Engine.
4. **Repo scaffolding (remaining)** — `web/` (Fastify gateway + Next.js portal),
   `infra/docker-compose.yml` for the four data stores, and `pnpm` workspace.

---

## Backlog (not yet scheduled)

- ADRs for open decisions in ARCHITECTURE.md §8 (codegen, canonical record
  ownership, embeddings/chunking, multilingual pipeline, auth provider).
- New blueprint sections flagged earlier but not written: **Legal & Liability**,
  **Platform Threat Model**, and a **Budget revision** (§25) to cover labeler
  compensation, certifications, data licensing, translation, and audits.

---

## Loop log (append-only, newest first)

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
