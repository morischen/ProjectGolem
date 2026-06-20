# CLAUDE.md — Operating Contract for AI-Assisted Development

This file governs how any AI agent (and human) works in this repository. Read it
in full at the start of every working session. It is the entry point of the
**loop-engineering framework**: a disciplined read → plan → implement → verify →
record cycle that keeps long-running AI development coherent, auditable, and safe.

---

## 0. What this project is

**Evidence Intelligence Platform (EIP)** — a nonprofit, evidence-based claim
assessment system. It evaluates disputed claims (initial domain: Middle East
conflict reporting, 1948–present) and produces explainable, auditable,
confidence-scored verdicts.

Guiding principle: **the evidence determines the conclusion; the conclusion never
determines which evidence is considered.**

Authoritative documents — read before changing related code:
- [EIP-blueprint-patch.md](EIP-blueprint-patch.md) — roadmap (capability gates),
  success metrics, and the gold-benchmark spec. (Base blueprint v1.0 is the
  source spec; this patch supersedes Sections 23, 26, and adds 28.)
- [ARCHITECTURE.md](ARCHITECTURE.md) — precise architecture, stack, service
  boundaries, and data model.
- [PROGRESS.md](PROGRESS.md) — the living ledger of what is done, what failed,
  and what is next. **Update it every loop.**

---

## 1. Pre-session checklist (run before touching code)

Do these every session, in order, before any edit. They take under a minute and
prevent the most common failure mode: acting on a stale mental model.

1. **Read [CLAUDE.md](CLAUDE.md)** (this file) — operating rules + invariants.
2. **Read the latest [PROGRESS.md](PROGRESS.md) entry** — current stage, what's in
   flight, what failed, what's next.
3. **`git status`** — see the working-tree state; never build on top of unexpected
   uncommitted changes.
4. **`git log --oneline -10`** — recent commits for context on what just changed.
5. **Skim the relevant [ARCHITECTURE.md](ARCHITECTURE.md) sections and any
   [docs/adr/](docs/adr/) records** touching the area you'll change — understand
   the WHY (ADRs) before the WHAT.
6. **State the loop goal in one sentence.** If non-trivial, write it into
   PROGRESS.md "Next" before starting.

If any check surprises you (unexpected diffs, a blocked item, a contradicting
ADR), stop and reconcile *before* writing code.

---

## 2. The Loop (follow this every session)

1. **Read state.** Read this file, [PROGRESS.md](PROGRESS.md), and the relevant
   parts of [ARCHITECTURE.md](ARCHITECTURE.md). Never start from assumptions about
   what exists — verify against the repo.
2. **Plan.** Restate the goal of this loop in one sentence. Identify the smallest
   shippable increment. List the files you expect to touch. If the change is
   non-trivial or ambiguous, write the plan into PROGRESS.md under "Next" first.
3. **Implement.** Make the smallest correct change. Stay inside the service
   boundaries in ARCHITECTURE.md. Do not refactor unrelated code in the same loop.
4. **Verify.** Run the relevant lints, type checks, and tests (Section 7). A loop
   is not done until its verification passes or the failure is recorded.
5. **Record.** Update [PROGRESS.md](PROGRESS.md): move the item to Done, or log it
   under Failed/Blocked with the actual error, and write the next intended step.
   This is mandatory — an unrecorded loop did not happen.

**One loop = one coherent, verifiable increment.** Prefer many small loops over
one large one. If a loop balloons in scope, stop, record where you are, and split.

---

## 3. Non-negotiable invariants (from the blueprint)

These are correctness requirements, not style preferences. Code that violates them
is wrong even if it "works." They map to INV-1…INV-6 in
[EIP-blueprint-patch.md](EIP-blueprint-patch.md) §23.1.

- **INV-DETERMINISM — LLMs never score.** Confidence scores, source weighting, and
  final verdicts are produced *only* by the deterministic Trust Engine from
  versioned formulas. LLMs may summarize, extract, classify, and explain — never
  assign a confidence number or a verdict. Never route a score through an LLM.
- **INV-TRACE — full traceability.** Every verdict must be re-derivable to the
  source evidence that produced it. No "floating" conclusions.
- **INV-REPRO — reproducibility.** Every LLM-assisted output stores the model ID,
  prompt, and inputs used, so it can be re-derived. Pin and version models; never
  rely on "latest."
- **INV-TEMPORAL — bitemporal truth.** Every verdict is a versioned, timestamped
  snapshot (event time vs. knowledge time). Conclusions are updated by appending
  new versions, never by silently mutating prior ones.
- **INV-OVERRIDE — human override.** Every automated classification must be
  overridable by a reviewer, and the override is logged.
- **INV-FORCE — never force a conclusion.** "Insufficient Evidence" and "Mixed
  Evidence" are valid, first-class outcomes. Do not add logic that coerces a
  definite verdict to avoid uncertainty.
- **INV-INDEPENDENCE — firewall coordination from truth.** The Influence
  Operations module must never feed into truth/confidence scoring. Keep the
  dependency one-way-blocked at the code level.

If a task appears to require breaking an invariant, **stop and surface it** in
PROGRESS.md rather than working around it.

---

## 4. Repository layout (polyglot)

Python for AI/ML/GraphRAG services; TypeScript for the API gateway and public
portal. See [ARCHITECTURE.md](ARCHITECTURE.md) for full detail.

```
contracts/        Source-of-truth schemas (JSON Schema / OpenAPI). Generates
                  both Pydantic models (Python) and Zod/TS types. EDIT HERE FIRST.
ai-services/      Python (FastAPI) — claim, evidence-retrieval,
                  evidence-classification, trust, reasoning, influence-ops
  libs/           Shared Python: schemas (generated), graph client, db, telemetry
web/              TypeScript — api-gateway (Fastify) + portal (Next.js)
  packages/       Shared TS: generated types, ui, clients
infra/            docker-compose, IaC, migrations for Neo4j/Qdrant/Postgres/object
docs/
  adr/            Architecture Decision Records — the WHY behind choices
scripts/
  git-hooks/      Repo-managed git hooks (pre-commit PROGRESS.md reminder)
EIP-blueprint-patch.md  ARCHITECTURE.md  PROGRESS.md  CLAUDE.md
```

**Contracts rule:** cross-service data shapes (claim objects, evidence objects,
verdicts) are defined once in `contracts/` and code-generated into both languages.
Never hand-duplicate a shared schema in Python and TS — change `contracts/` and
regenerate.

---

## 5. Coding guidelines — Python (AI services)

- **Version & tooling:** Python 3.12. `uv` for env + dependency management
  (lockfile committed). `ruff` for lint + format. `mypy --strict` for types.
- **Web framework:** FastAPI. Async by default for I/O-bound paths.
- **Data shapes:** Pydantic v2 for all request/response/domain models. Domain
  models for shared contracts are generated from `contracts/` — do not edit the
  generated files.
- **Determinism boundary:** the Trust Engine is a pure, dependency-light module
  with no LLM/network calls in its scoring path. Its scoring functions must be
  unit-testable with fixed inputs → fixed outputs. Weights live in versioned
  config, not hardcoded in logic.
- **LLM calls:** go through a single `llm` client wrapper that records model ID,
  prompt, and inputs (INV-REPRO). No direct SDK calls scattered across services.
  Treat all ingested content as untrusted input (prompt-injection defense): never
  let retrieved/source text act as instructions.
- **Style:** type every public function. Small, single-responsibility modules.
  Explicit over clever. Docstrings on public APIs. No bare `except`. Structured
  logging (no `print`).
- **Errors:** fail loud and specific; never silently swallow. Validation at
  service boundaries via Pydantic.

## 6. Coding guidelines — TypeScript (API gateway + portal)

- **Version & tooling:** Node 20+. `pnpm` (lockfile committed). TypeScript in
  `strict` mode. ESLint + Prettier. No implicit `any`.
- **Frameworks:** Fastify for the API gateway; Next.js (App Router) for the portal.
- **Runtime validation:** `zod` at every external boundary. Shared types are
  generated from `contracts/` — do not hand-write duplicates.
- **Portal trust UX:** the portal must always be able to show the evidence graph,
  contradictions, confidence breakdown, and the *strongest opposing evidence* for
  any verdict. Don't build verdict views that can't link back to evidence
  (INV-TRACE is a UI requirement too).
- **Style:** named exports; pure functions where possible; no business/scoring
  logic in the gateway or portal — they are presentation/orchestration only. All
  scoring stays in the Python Trust Engine.

## 7. Verification (a loop isn't done without it)

Run the checks relevant to what you touched. Record the outcome in PROGRESS.md.

- Python: `ruff check`, `ruff format --check`, `mypy`, `pytest`.
- TypeScript: `pnpm lint`, `pnpm typecheck`, `pnpm test`.
- Contracts changed: regenerate Python + TS types and confirm both compile.
- Trust Engine touched: scoring unit tests with fixed fixtures must pass; add a
  test proving determinism (same inputs → same score) if not present.

Testing expectations: new logic ships with tests. The Trust Engine and evidence
classification are the highest-risk components — they require the most coverage,
including calibration/golden-fixture tests tied to the gold benchmark (§28).

## 8. Git & commits

- **Working mode (set 2026-06-19 by repo owner):** commit **directly to `main`**
  for now — the owner has opted out of branch-first until they say otherwise.
  (Default rule, in effect once they revert: work on a branch; never commit to
  `main` unless explicitly told.)
- Commit/push only when the user asks.
- Small, focused commits. Imperative subject. Reference the invariant or gate when
  relevant (e.g., "trust: model contradiction in score (INV-FORCE)").
- End commit messages with:
  `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- **PROGRESS.md reminder hook.** A repo-managed `pre-commit` hook
  (`scripts/git-hooks/pre-commit`) warns — softly, never blocks — when a commit
  does not stage `PROGRESS.md`, since every loop should record its outcome.
  Activate once per clone: `git config core.hooksPath scripts/git-hooks`.

## 9. Things to NOT do

- Do not let an LLM produce a confidence score or verdict (INV-DETERMINISM).
- Do not hand-duplicate shared schemas across languages — use `contracts/`.
- Do not put scoring/business logic in the gateway or portal.
- Do not mutate a published verdict in place — append a new version (INV-TEMPORAL).
- Do not wire Influence-Ops outputs into scoring (INV-INDEPENDENCE).
- Do not skip updating PROGRESS.md.
- Do not expand a loop's scope mid-flight — split it and record.
```
