# ARCHITECTURE.md — Evidence Intelligence Platform

Precise architecture, technology stack, service boundaries, and data model.
This is the technical source of truth. The product/governance source of truth is
the base blueprint (v1.0) plus [EIP-blueprint-patch.md](EIP-blueprint-patch.md).
Operating rules and coding guidelines are in [CLAUDE.md](CLAUDE.md).

Status: **greenfield** — this document describes the target design. Nothing is
built yet. Track build state in [PROGRESS.md](PROGRESS.md).

---

## 1. Architectural principles

1. **Separation of judgment from scoring.** LLMs do language work (extract,
   classify, summarize, explain). A deterministic Trust Engine does all scoring.
   The boundary is architectural, not just conventional. (INV-DETERMINISM)
2. **Everything traces to evidence.** No verdict exists without a re-derivable
   chain to its source evidence. (INV-TRACE)
3. **Reproducible by construction.** Every LLM output stores model ID + prompt +
   inputs. Models are pinned/versioned. (INV-REPRO)
4. **Bitemporal.** Verdicts and evidence are versioned snapshots: event time
   (when it happened / was published) vs. knowledge time (when we learned it).
   Conclusions update by appending versions. (INV-TEMPORAL)
5. **Uncertainty is first-class.** "Insufficient" and "Mixed" are valid outputs;
   nothing forces a definite verdict. (INV-FORCE)
6. **Coordination is firewalled from truth.** Influence-Ops never feeds scoring.
   (INV-INDEPENDENCE)

---

## 2. Technology stack

### Application
| Concern | Choice | Notes |
|--------|--------|------|
| AI/ML/GraphRAG services | **Python 3.12 + FastAPI** | LLM SDKs, ML, graph/vector clients are first-class here |
| API gateway | **TypeScript (Node 20) + Fastify** | Auth, routing, rate-limiting, orchestration only — no scoring |
| Public portal | **TypeScript + Next.js (App Router)** | Transparency surface: evidence graph, contradictions, confidence breakdown |
| Shared contracts | **JSON Schema / OpenAPI in `contracts/`** | Code-generated into Pydantic (Py) + Zod/TS types |

### Data stores (fixed by blueprint §15)
| Store | Choice | Holds |
|------|--------|------|
| Graph DB | **Neo4j** (alt: Memgraph) | Knowledge graph: entities, claims, evidence, sources, edges |
| Vector DB | **Qdrant** (alt: Weaviate/Pinecone) | Embeddings for semantic retrieval |
| Metadata DB | **PostgreSQL** | Claims/verdicts/audit/users; bitemporal versioning; source-reliability config |
| Object storage | **S3-compatible** (MinIO in local dev) | Raw documents, PDFs, media, satellite imagery |

### Cross-cutting
- **LLM access:** single wrapper client (records model+prompt+inputs; pinned model IDs). Default to the latest, most capable Claude models for language tasks.
- **AuthN/AuthZ:** OIDC; RBAC; MFA for reviewer/admin roles.
- **Audit:** append-only audit log (immutable); PII segregated for GDPR/CCPA erasure (crypto-shredding) — resolve the immutability/erasure tension by logging *decisions + public evidence* immutably and keeping personal data separately erasable.
- **Observability:** structured logging, tracing, metrics. Calibration/bias dashboards (blueprint §23/§26) are built on these.

---

## 3. Repository layout

```
contracts/                 JSON Schema / OpenAPI — source of truth for shared shapes
  claim.schema.json        normalized claim object
  evidence.schema.json     evidence object + classification
  verdict.schema.json      verdict snapshot (bitemporal)
  codegen/                 generators -> Pydantic + Zod/TS

ai-services/               Python (FastAPI)
  claim-engine/
  evidence-retrieval/
  evidence-classification/
  trust-engine/            DETERMINISTIC — no LLM/network in scoring path
  reasoning-engine/        LLM explanations — never scores
  influence-ops/           FIREWALLED from scoring
  libs/
    schemas/               generated Pydantic models (do not hand-edit)
    graph/                 Neo4j client + queries
    vectors/               Qdrant client
    db/                    Postgres access + bitemporal helpers
    llm/                   LLM wrapper (records model+prompt+inputs)
    telemetry/             logging/metrics/tracing

web/                       TypeScript
  api-gateway/             Fastify — auth, routing, rate-limit, orchestration
  portal/                  Next.js — public transparency UI
  packages/
    types/                 generated Zod/TS types (do not hand-edit)
    api-client/            typed client for ai-services
    ui/                    shared components

infra/                     docker-compose (neo4j/qdrant/postgres/minio), IaC, migrations
docs/
  adr/                     Architecture Decision Records (the WHY) — see docs/adr/README.md
scripts/git-hooks/         repo-managed git hooks (pre-commit PROGRESS.md reminder)
```

---

## 4. Services

### 4.1 API Gateway (TS / Fastify)
Entry point for all clients. AuthN/Z, rate-limiting, request validation,
orchestration of AI-service calls, response shaping. **No scoring or business
logic.** Enforces submission rate limits and abuse/reputation gating (blueprint
§23 G2.x).

### 4.2 Claim Engine (Py)
Normalizes raw input (text, URL, social post, article, PDF, transcript) into a
structured **claim object**. Extraction, entity recognition, event detection, and
the **claim-type taxonomy** (empirical / legal / definitional / predictive /
normative — drives downstream handling). LLM-assisted; output validated against
`contracts/claim.schema.json`.

### 4.3 Evidence Retrieval Engine (Py)
Multi-source retrieval across the four source tiers (primary / trusted reporting /
context / emerging). Citation generation, evidence ranking, contradiction
discovery. Uses Qdrant (semantic) + Neo4j (relationship traversal). Performs
**independence analysis** via the graph (shared-origin / citation-cycle detection)
to resist citation laundering.

### 4.4 Evidence Classification Engine (Py)
Classifies each evidence item's relationship to the claim: **Supports /
Contradicts / Neutral / Inconclusive**, with per-item rationale and an LLM
confidence on the *classification* (not the verdict). High-impact claims get
multi-pass classification (model+model or model+human). **This is a scoring input
even though it's LLM-driven** — it carries override paths (INV-OVERRIDE) and full
reproducibility (INV-REPRO).

### 4.5 Trust Engine (Py) — DETERMINISTIC
The only component that produces confidence and verdicts. Pure functions, no
LLM/network in the scoring path. Inputs: classified evidence + source-reliability
config + corroboration/independence/freshness signals. Implements the versioned
weighted formula (blueprint §10), with weights in versioned config and
**domain/claim-type awareness**, and models **contradiction as a downward force**
(not just a label). Emits a verdict from the allowed set:
Verified / Likely True / Mixed / Insufficient / Likely False / False — as a
**bitemporal verdict snapshot**. Must be fully unit-testable (fixed inputs →
fixed score) and calibration-tested against the gold benchmark (§28).

### 4.6 Reasoning Engine (Py)
LLM-generated human-readable explanations, reasoning chains, and historical
context. Consumes the Trust Engine's output; **never determines scores**.

### 4.7 Influence Operations Module (Py) — FIREWALLED
Coordination score, bot likelihood, amplification indicators from account/network
behavior. Outputs are reported alongside claims but **structurally blocked from
feeding scoring** (INV-INDEPENDENCE). One-way isolation enforced in code.

### 4.8 Human Review (workflow, spans services)
Escalation queue triggered by low confidence (<70%), high-impact topics, evidence
conflict over threshold, or appeals. Reviewer profiles: historians, journalists,
researchers, OSINT. Carries reviewer calibration tracking, blind/diverse-panel
review for high-impact items, and logged overrides.

---

## 5. Knowledge graph model

**Node types:** Person, Organization, Government, Military Group, Location, Event,
Claim, Evidence, Document, Source.

**Edge types:** supports, contradicts, references, mentions, reported_by,
investigated_by, occurred_at, linked_to.

Shape (per blueprint §14):
```
Event
├── Claim A ── Evidence A, Evidence B, Source A
└── Claim B ── Evidence C, Source B
```
The graph is also the substrate for independence/citation-laundering analysis
(§4.3) — a key reason GraphRAG is used over plain document similarity.

---

## 6. Primary data flow (claim → verdict)

```
Client
  → API Gateway (auth, validate, rate-limit)
    → Claim Engine            normalize → claim object (typed)
    → Evidence Retrieval      gather + rank + find contradictions + independence
    → Evidence Classification Supports/Contradicts/Neutral/Inconclusive (+rationale)
    → Trust Engine            DETERMINISTIC score + verdict snapshot (bitemporal)
    → Reasoning Engine        human-readable explanation (no scoring)
  ← Gateway assembles response (verdict + evidence graph + contradictions +
    confidence breakdown + strongest opposing evidence)
  → Audit log (append-only), Knowledge graph + Postgres updated (versioned)
```
Human Review can intercept at the Trust Engine boundary; Influence-Ops runs in
parallel and is attached to the response but **never** to the score.

---

## 7. Reproducibility & temporal model

- Every LLM-assisted artifact (extraction, classification, explanation) is stored
  with `{model_id, prompt, inputs, output, timestamp}`.
- Verdicts are **append-only versioned snapshots** keyed by claim + knowledge
  time; the prior version is retained. "What did we conclude on date X, and why
  did it change?" must always be answerable (INV-TEMPORAL, INV-TRACE).
- Source-reliability config and Trust Engine weights are **versioned**; a verdict
  records which config version produced it, so old verdicts remain reproducible.

---

## 8. Architectural decisions (recorded as ADRs in [docs/adr/](docs/adr/))

The decisions once open here are now recorded as ADRs (Accepted = settled; Proposed =
direction agreed, implementation pending):

- Contract codegen toolchain — [ADR-0004](docs/adr/0004-contract-codegen-toolchain.md)
  (Accepted).
- Graph vs. Postgres ownership of canonical claim/verdict records: Postgres canonical
  + Neo4j projection — [ADR-0010](docs/adr/0010-canonical-record-ownership.md)
  (Accepted).
- Embedding model + chunking strategy for Qdrant —
  [ADR-0011](docs/adr/0011-embeddings-and-chunking.md) (Proposed).
- Multilingual pipeline (Arabic/Hebrew/English per §23 L0): originals authoritative,
  translate for processing, parity measured —
  [ADR-0012](docs/adr/0012-multilingual-pipeline.md) (Proposed).
- Auth provider: API keys for services now, OIDC for humans later —
  [ADR-0013](docs/adr/0013-auth-provider-oidc.md) (Proposed).
