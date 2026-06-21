# Admin Portal — Implementation Plan (A1–A4)

Status: **proposed** (not started). A full operator surface to **review and adjust
all aspects** of EIP. This is a large, multi-loop initiative: most capabilities need
**new backend admin APIs first**, then a new admin UI. Built incrementally, each
phase delivered as green, committed loops (build → QA + smoke → commit/push).

## Why it's not trivial
- The public portal ([web/portal](../web/portal)) is read-only; today there is **no**
  list/search, review queue, config, appeals, key-management, or audit UI.
- Changing scoring weights / source reliability is a **credibility-critical control**
  (blueprint §20) — it must be versioned, **audited**, and change-controlled, not a
  raw form. So the admin portal also forces real backend work (audit log, config
  store, key store) we've deferred.

---

## Cross-cutting foundations (established in A1, used throughout)

1. **Auth — `admin` scope.** Reuse the gateway's API-key scopes
   ([auth.ts](../web/api-gateway/src/auth.ts)); admin routes require scope `admin`.
   OIDC/MFA is a later backlog item, not a blocker.
2. **`/admin/*` gateway routes.** All admin traffic goes through the gateway under
   `/admin/*`, `admin`-scoped + rate-limited, proxying to per-service admin APIs.
3. **New `web/admin` Next.js app.** Separate from the public portal (different trust
   boundary, different auth). Added to the pnpm workspace, QA gate, and CI. Hermetic
   tests (vitest + mocked fetch); a key is entered at login and sent as `x-api-key`.
4. **Audit everything that writes.** A new append-only `AuditStore` in
   `eip-persistence` (actor, action, target, before/after, timestamp) records every
   admin mutation. Introduced in A2 (first writes), reused after.
5. **Read-before-write.** Each area ships read-only first, then guarded + audited edit.
6. **Determinism preserved.** Config becomes versioned *data*, but scoring stays
   deterministic per config version (INV-DETERMINISM/INV-REPRO) — verdicts already
   record `weights_version`.

---

## A1 — Read-only admin foundation (claims & verdicts browser)
**Goal:** an authenticated admin can browse claims, verdicts, version history, and
the evidence/breakdown behind each. Lowest risk; immediately useful.

**Backend**
- `eip-persistence`: add `list_claims()` (paginated) to `VerdictStore` (in-memory +
  SQL).
- Trust Engine: `GET /v1/claims` (list, paginated/filterable). (History endpoints
  already exist.)
- Gateway: `admin`-scoped proxies — `GET /admin/claims`, `/admin/claims/{id}/verdicts`,
  `/admin/claims/{id}/verdict`. (Finally exposes verdict history through the gateway.)

**Frontend (`web/admin`)**
- Scaffold the app (mirrors portal); login (enter API key → session); a typed
  `AdminClient`.
- **Claims list** page (search/paginate); **Claim detail** page — verdict, confidence
  breakdown, **version timeline** (bitemporal), evidence, independence summary.

**Verification:** `list_claims` store tests; gateway admin-route tests (401/403/200,
mocked fetch); admin UI vitest (render, auth-gating) — all hermetic.

**Dependencies:** gateway auth (exists), bitemporal store (exists).

---

## A2 — Scoring config & source reliability (view → guarded edit + audit)
**Goal:** view and (guardedly) adjust scoring weights, thresholds, and
source-tier reliability — the core "adjust the methodology" capability.

**Backend**
- `eip-persistence`: **`AuditStore`** (append-only action log) + **`ConfigStore`**
  (versioned `ScoringWeights`, seeded from `DEFAULT_WEIGHTS`/`HISTORICAL_WEIGHTS`).
  Weights move from static constants to versioned *data*.
- Trust Engine: `GET /v1/config` (active config + profiles + versions); `POST /v1/config`
  → creates a **new** config version (never mutates), writes an audit entry; scoring
  reads the active version. Source reliability (`tier_reliability`) edited via the
  same config.
- Gateway: `admin`-scoped `GET/POST /admin/config`.

**Frontend**
- **Config** page: view weights/thresholds/tier-reliability; edit form with live
  "sum-to-1.0" validation; on save show new **version + diff**; show change history.

**Governance:** every change versioned + audited + attributed; surfaced as a public
changelog (blueprint §20). Future: multi-approver change-control.

**Verification:** `ConfigStore`/`AuditStore` hermetic tests; config endpoints
(read/write, audit recorded, new version on edit, sum-to-1 rejection); UI tests.

**Dependencies:** A1 (admin shell, audit foundation).

---

## A3 — Human review queue & appeals  ✅ DONE (2026-06-21)
**Goal:** the escalation workflow (FR-007) and a real appeals loop — reviewers see
queued items and record overrides; the public can file appeals that land in the queue.

Delivered: `ReviewStore` (in-memory + SQL); Trust Engine `/v1/review` +
`/v1/appeals` with score-time auto-enqueue and override → new `human-override`
verdict version + audit (INV-OVERRIDE); gateway `admin` review/appeals routes + a
public `POST /v1/appeals`; admin Review/Appeals UI; live public `AppealEntry`.

**Backend**
- `ReviewStore` (queue of items needing review: confidence < 70%, evidence conflict,
  or appeals) + endpoints: list queue, get item, **submit decision/override**.
- Override → appends a **new verdict version** with reviewer attribution (bitemporal
  store + audit) — realizes INV-OVERRIDE.
- **Appeals API**: submit (new evidence / source challenge / methodology), list,
  respond; appeals **logged publicly**. Public-portal `AppealEntry` becomes functional
  (POSTs an appeal → creates a queue item).
- Gateway: `admin`-scoped review/appeals routes; a public appeal-submit route.

**Frontend**
- Admin **Review queue** (list/filter) + item detail with override action; **Appeals
  management** page. Wire the public portal's appeal button to the submit route.

**Verification:** `ReviewStore`/appeals hermetic tests; override → new version +
audit; queue endpoints; admin UI + portal appeal-submit tests.

**Dependencies:** A1, A2 (audit).

---

## A4 — Calibration/bias dashboard & access management  ✅ DONE (2026-06-21)
**Goal:** surface the trust metrics and manage who can do what.

Delivered: Trust Engine `GET /v1/metrics` (benchmark accuracy/ECE + queue health +
claims count) and central `POST /v1/audit`; gateway `KeyStore` (SHA-256-hashed,
env-seeded) with admin `/admin/metrics` + `/admin/keys` CRUD; admin Dashboard and
Access-management pages. Note: metrics are a live snapshot (a persistent calibration
ledger §28.12 and DB-backed KeyStore/OIDC remain future work).

**Backend**
- **Metrics endpoint**: serve calibration + benchmark results (verdict accuracy, ECE,
  bias delta, independence stats) from stored runs; back the **calibration ledger**
  (§28.12). Reuses the calibration harness ([e2e/calibration.py](../ai-services/e2e/calibration.py))
  and the gold benchmark.
- **`KeyStore`**: move API keys/roles from `EIP_API_KEYS` env to a managed store with
  admin CRUD (audited). (Bridge toward OIDC later.)
- Gateway: `admin`-scoped `/admin/metrics`, `/admin/keys`.

**Frontend**
- **Dashboard**: calibration/bias charts, queue health, review throughput (the §23/§26
  gate metrics). **Access management**: keys/roles CRUD.

**Verification:** metrics endpoint (hermetic with seed/benchmark); `KeyStore` hermetic;
dashboard + access UI tests.

**Dependencies:** A1–A3; calibration harness + benchmark (exist).

---

## Sequencing & effort
A1 → A2 → A3 → A4, each **several loops**. A1 is the safe, useful start (read-only,
no destructive surface). A2 introduces the audit log + config-as-data (the highest-
leverage and most governance-sensitive step). A3 is workflow-heavy. A4 is metrics +
access. Full real-data operation needs the data stores (Postgres) up; hermetic CI uses
in-memory/SQLite stores + mocked fetch throughout.

## Out of scope (separate backlog)
OIDC/MFA, distributed rate-limit store, Influence-Ops module, multilingual UI,
deployment/observability, real embedding model + graph seeding.
