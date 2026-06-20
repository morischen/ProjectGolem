# Evidence Intelligence Platform (EIP) — Blueprint Patch

## Patch Version
1.2 — Consolidated revisions to the EIP Comprehensive Blueprint (base v1.0)

## Scope of this Patch
This document supersedes / adds the following sections of the base blueprint:

- **Section 23 — Roadmap** → replaced by a **Capability-Gated Roadmap**.
- **Section 25 — Budget Estimates** → revised (adds the line items the original omitted).
- **Section 26 — Success Metrics** → revised to align with measurable gate metrics.
- **Section 28 — Gold Benchmark Design Specification** → new section (the measuring instrument the gates depend on).
- **Section 29 — Legal & Liability** → new section (v1.2).
- **Section 30 — Platform Threat Model** → new section (v1.2).

Apply by replacing Sections 23, 25, 26 in the base document with the versions below and appending Sections 28, 29, 30. All other sections of base v1.0 remain in force. Cross-references: the roadmap gates (Section 23) are computed from the benchmark (Section 28); the success metrics (Section 26) reuse the benchmark metric definitions (28.10); the threat model (Section 30) and legal posture (Section 29) reference controls already implemented in code (ADRs 0003/0005/0007/0008).

---

# 23. Capability-Gated Roadmap

## 23.0 Rationale

The platform does not advance by calendar date. It advances by **demonstrated evidence quality**. Each stage has hard, measurable **exit gates**; the platform cannot progress to the next stage — and in particular cannot expose verdicts to a wider audience — until every gate is met and independently verified.

This protects the core asset (credibility): a methodological failure caught at Stage 1 is a learning; the same failure at public scale is an institutional death blow. Dates are *forecasts*, not commitments. Gates are commitments.

**Two rules govern progression:**
1. **No gate, no gate-crossing.** A stage ships when its metrics clear, not when its quarter ends.
2. **Exposure trails confidence.** Audience size and claim difficulty expand only as calibration and bias metrics prove out.

---

## 23.1 Cross-Cutting Invariants (must hold at every stage from Stage 1 onward)

These are not milestones; they are continuous conditions. Violation halts progression and may trigger rollback (see 23.9).

| ID | Invariant | Threshold |
|----|-----------|-----------|
| INV-1 | **Traceability** — every published verdict re-derivable to source evidence | 100% |
| INV-2 | **Reproducibility** — every verdict re-derivable from stored model ID + prompt + inputs | >= 99% |
| INV-3 | **Temporal integrity** — every verdict is a versioned, timestamped snapshot (bitemporal) | 100% |
| INV-4 | **Determinism of scoring** — confidence produced by versioned formula, never by LLM | 100% |
| INV-5 | **Human override path** — every automated classification can be overridden and logged | 100% |
| INV-6 | **Correction latency** — published error corrected/retracted within SLA once confirmed | <= 72h |

---

## 23.2 Maturity Overview

| Stage | Name | Audience | Verdicts public? | Forecast |
|-------|------|----------|------------------|----------|
| L0 | Foundations / Methodology Lab | Internal only | No | ~Months 0-4 |
| L1 | Closed Pilot | Internal + expert panel | No | ~Months 3-8 |
| L2 | Limited Public Beta | Invited / labeled experimental | Yes (flagged) | ~Months 7-13 |
| L3 | Public Platform | General public | Yes | ~Months 12-20 |
| L4 | Scale & Breadth | Public + API/extension | Yes | ~Months 18-30 |
| L5 | Institution | Global, multi-domain | Yes | ~30+ |

Stages overlap because work on the next stage begins before the current stage's gates close; **gate-crossing does not.**

---

## 23.3 Stage L0 — Foundations / Methodology Lab

**Purpose:** Build the machinery and the measuring instruments *before* assessing anything publicly. The deliverable is not verdicts — it's a methodology you can prove is sound.

**Capabilities delivered:**
- Claim engine (extraction, entity recognition, event detection, claim-type taxonomy: empirical / legal / definitional / predictive / normative)
- Evidence retrieval (multi-source) + GraphRAG foundation
- Deterministic Trust Engine v0 (versioned weights; contradiction modeled, not just labeled)
- Bitemporal data model + verdict versioning
- Reproducibility harness (pinned models, stored prompts/inputs)
- **Gold benchmark dataset v1** — expert-labeled claims with known resolutions, including matched claim pairs across opposing framings for bias testing (see Section 28)
- Multilingual ingestion for the launch region (Arabic + Hebrew + English at minimum)

**Exit gates (all required):**

| Gate | Metric | Threshold |
|------|--------|-----------|
| G0.1 | Benchmark exists | >= 300 labeled claims, >= 3 independent expert labels each |
| G0.2 | Inter-rater reliability on gold labels | Fleiss' kappa >= 0.6 |
| G0.3 | Claim-extraction precision/recall vs. gold | >= 0.85 / >= 0.80 |
| G0.4 | Citation accuracy (cited source supports statement) | >= 0.90 |
| G0.5 | Reproducibility harness operational | INV-2 met on benchmark |
| G0.6 | Multilingual parity (verdict stability across source language) | <= 5% divergence on translated duplicate set |

**Risks retired:** "Can we even extract and structure claims reliably?" "Is our benchmark trustworthy?"

---

## 23.4 Stage L1 — Closed Pilot

**Purpose:** Run the full pipeline on a *narrow, hard* claim set with experts in the loop. Discover where evidence quality and calibration break. No public exposure.

**Capabilities delivered:**
- Evidence Classification Engine (Supports/Contradicts/Neutral/Inconclusive) with per-classification rationale + confidence
- Confidence/Trust Engine v1 (domain- and claim-type-aware weights)
- Human review workflow + reviewer calibration tracking
- Multi-pass classification for high-impact claims (model + model, model + human)
- Independence/citation-laundering detection via graph (shared-source, citation-cycle analysis)

**Exit gates (all required):**

| Gate | Metric | Threshold |
|------|--------|-----------|
| G1.1 | **Calibration** — Expected Calibration Error on gold set | ECE <= 0.10 |
| G1.2 | **Bias symmetry** — confidence delta on matched opposing-framing claim pairs | <= 0.05 |
| G1.3 | Evidence-classification agreement with expert panel | kappa >= 0.65 |
| G1.4 | Reviewer inter-rater reliability | kappa >= 0.6 |
| G1.5 | Independence detection catches seeded laundering cases | >= 0.80 recall on red-team set |
| G1.6 | "Insufficient/Mixed" correctly assigned to genuinely undecidable claims | >= 0.85 on adversarial-ambiguous subset |

**Legal/governance pre-conditions for L2 (must be in place before any public verdict):**
- Defamation/liability strategy + insurance bound
- Correction & retraction policy live (INV-6 tested)
- Funding-transparency + COI/recusal framework ratified by board
- First independent bias audit commissioned

**Risks retired:** "Are our verdicts calibrated?" "Are we systematically biased?" "Will reviewers agree?" "Are we legally exposed?"

---

## 23.5 Stage L2 — Limited Public Beta

**Purpose:** Expose verdicts to a controlled, informed audience under an explicit "experimental" label. Test the *public-facing transparency surface* and the appeals loop with real adversarial users — while exposure is still contained.

**Capabilities delivered:**
- Public portal (read-only): evidence graph, contradictions, confidence breakdown, "strongest opposing evidence" view
- Confidence engine public-facing (bands, not false-precision point estimates)
- Historical context engine
- Public audit trail
- Appeals process (new evidence / source challenge / methodology concern), publicly logged
- Submission rate-limiting + abuse/reputation gating

**Exit gates (all required):**

| Gate | Metric | Threshold |
|------|--------|-----------|
| G2.1 | Calibration holds on *live* (non-benchmark) resolved claims | ECE <= 0.12 |
| G2.2 | First independent bias audit | No systematic skew at p<0.05; findings published |
| G2.3 | Appeal resolution quality | >= 80% of upheld appeals traced to a real methodology/evidence fix |
| G2.4 | Transparency comprehension (user can locate evidence chain) | >= 75% task success in user testing |
| G2.5 | Pipeline integrity under attack | Red-team evidence-poisoning + prompt-injection campaign fails to flip >= 95% of targeted verdicts |
| G2.6 | Review queue economically sustainable | Escalation volume <= reviewer throughput at steady state |

**Risks retired:** "Can the public understand and trust the transparency surface?" "Does the platform survive adversarial users?" "Does the appeal loop actually improve the system?"

---

## 23.6 Stage L3 — Public Platform

**Purpose:** Open to the general public on the launch domain. This is the first *unflagged* public claim of credibility.

**Capabilities delivered:**
- Full public access, all launch-domain claim types
- Limited public API (rate-limited, attributed)
- Hardened operations (99.9% uptime SLA, SOC2/ISO27001 certification complete)
- Continuous calibration + bias dashboards (public)

**Exit gates (all required):**

| Gate | Metric | Threshold |
|------|--------|-----------|
| G3.1 | Sustained calibration over >= 2 quarters | ECE <= 0.10, no upward drift |
| G3.2 | Two consecutive independent bias audits clean | published |
| G3.3 | Security certifications | SOC2 Type II + ISO27001 obtained |
| G3.4 | Correction SLA adherence | >= 95% within 72h over trailing quarter |
| G3.5 | External academic methodology review | >= 1 peer-reviewed or institutionally endorsed assessment |

**Risks retired:** "Is the institution operationally and credibly ready to stake its public reputation?"

---

## 23.7 Stage L4 — Scale & Breadth

**Purpose:** Expand surface area only after the core is proven. Each *new region/language/domain* re-runs its own L0-L2 gates on its own benchmark before public exposure — credibility is not transferable across domains automatically.

**Capabilities delivered:**
- Browser extension
- Full public API
- Influence Operations module (firewalled from scoring — see Section 18)
- Additional languages/regions (each gated independently)
- Research partnerships

**Exit gates:**

| Gate | Metric | Threshold |
|------|--------|-----------|
| G4.1 | Each new domain passes its own L0-L2 gates before launch | per-domain |
| G4.2 | Influence-ops/scoring independence verified | zero scoring leakage in audit |
| G4.3 | API/extension abuse controls | red-team pass |
| G4.4 | Cross-domain calibration parity | ECE <= 0.12 per domain |

---

## 23.8 Stage L5 — Institution

**Purpose:** Multi-domain standard-setting body. Expansion into elections, health, economic claims, etc., each via the same gated process.

**Exit gates:** Per-domain L0-L3 gates + sustained multi-year calibration/bias track record + third-party adoption metrics (Section 26).

---

## 23.9 Rollback Triggers

Any of the following **demotes** the platform to the prior stage (or pauses verdicts on the affected domain) until remediated:

- Invariant violation (INV-1...6)
- Calibration drift: ECE exceeds stage threshold for two consecutive measurement windows
- Bias audit failure (systematic skew detected)
- Confirmed evidence-poisoning or prompt-injection that flipped a published verdict
- Correction-SLA breach trend

Rollbacks are logged publicly (consistent with Section 20).

---

## 23.10 Mapping to the Original Calendar Phases

| Original Phase | Now governed by |
|----------------|-----------------|
| Phase 1 (claim/evidence/GraphRAG/manual review) | L0 + L1 |
| Phase 2 (portal/confidence/history/audit) | L2 |
| Phase 3 (influence/extension/API) | L4 (gated) |
| Phase 4 (multi-language/regions/partnerships) | L0-L2 *per domain*, not a single phase |

Key changes: **multilingual is pulled into L0** (the platform cannot adjudicate Arabic/Hebrew sources via English from day one), and **region expansion is no longer a single late phase** — each region earns public exposure on its own merits.

---

# 26. Success Metrics (Revised)

All metrics below are defined operationally and, where applicable, computed against the gold benchmark (Section 28.10) so that Section 23 gates and Section 26 reporting use the **same definitions**. Each metric names its measurement source and cadence.

## 26.1 Methodology Quality (the credibility core)

| Metric | Definition | Source | Cadence | Target |
|--------|------------|--------|---------|--------|
| Calibration (ECE) | Expected Calibration Error: do High-band verdicts resolve correctly at the High-band rate? | Benchmark + live resolved claims | Per release + quarterly | <= 0.10 |
| Bias delta | Mean confidence/verdict divergence across matched opposing-framing pairs | Benchmark (28.5) | Per release | <= 0.05 |
| Anchor gap | Calibration delta between out-of-domain neutral anchors and in-domain claims | Benchmark (28.7.6) | Quarterly | minimized; monitored |
| Undecidability recall | Correct Mixed/Insufficient assignment on ambiguous-by-design set | Benchmark (28.7.3) | Per release | >= 0.85 |
| Anti-evasiveness | High confidence correctly expressed on trivial controls | Benchmark (28.7.5) | Per release | >= 0.95 |
| Hindsight correctness | Correct pre-cutoff verdict + correct post-cutoff update | Benchmark (28.7.4) | Quarterly | tracked |

## 26.2 Technical Quality

| Metric | Definition | Source | Target |
|--------|------------|--------|--------|
| Claim-extraction P/R | Precision/recall of extracted claims and entities vs. gold | Benchmark (28.10) | >= 0.85 / >= 0.80 |
| Citation accuracy | Fraction of citations that actually support the cited statement | Benchmark | >= 0.90 |
| Classification kappa | Agreement of evidence classification with expert panel | Benchmark | >= 0.65 |
| Retrieval precision | Relevant evidence retrieved / evidence retrieved | Eval set | tracked, improving |
| Evidence coverage | Fraction of resolvable claims with sufficient evidence retrieved | Eval set | tracked, improving |
| Language parity | Verdict divergence on translated-duplicate set | Benchmark (28.7) | <= 5% |
| Poison/injection resistance | Verdict-flip rate under adversarial sets | Benchmark (28.7.1/.2) | flip rate <= 5% |
| Reproducibility | Verdicts re-derivable from stored model+prompt+inputs (INV-2) | Audit | >= 99% |

## 26.3 Trust & Governance

| Metric | Definition | Target |
|--------|------------|--------|
| Independent bias audits | Cadence and pass rate of third-party bias audits | >= 2/yr, published, no systematic skew |
| Appeal resolution quality | Upheld appeals traced to a real methodology/evidence fix | >= 80% |
| Correction SLA adherence | Confirmed errors corrected within 72h | >= 95% |
| Calibration ledger published | Public record of past verdicts vs. later-known outcomes | live and current |
| Funding transparency | Donor list + firewall attestations published | current |

## 26.4 Operational

| Metric | Definition | Target |
|--------|------------|--------|
| Availability | Uptime against SLA | 99.9% |
| Review turnaround | Median time from escalation to resolved verdict | tracked; within reviewer capacity |
| Review queue health | Escalation volume vs. reviewer throughput | <= 1.0 (sustainable) |

## 26.5 Impact (lagging indicators — never used to justify lowering 26.1 bars)

| Metric | Definition |
|--------|------------|
| Academic adoption | Citations, partnerships, methodology endorsements |
| Media adoption | Use by newsrooms; reference in reporting |
| Public usage | Active users, claims assessed, transparency-surface engagement |
| NGO partnerships | Formal collaborations |

**Guardrail:** Impact metrics (26.5) are explicitly subordinate. Growth or adoption never justifies relaxing methodology-quality (26.1) or trust (26.3) thresholds. A more popular but less calibrated platform is a regression.

---

# 28. Gold Benchmark Design Specification

## 28.0 Role in the System

The gold benchmark is the **measuring instrument** for the entire platform. Every progression gate in Section 23 (calibration ECE, bias deltas, classification kappa, citation accuracy) is computed against it. If the benchmark is biased, incomplete, or contaminated, every downstream credibility claim is void.

Therefore the benchmark is held to a *higher* evidentiary standard than the platform itself, and its construction is governed as a first-class institutional artifact — not an engineering dataset.

**Core tension this spec must resolve:** establishing "ground truth" on Middle East conflict claims without importing the very bias the platform exists to avoid. The design's answer is *not* to assert truth, but to **only admit claims whose resolution is independently and durably established**, and to make *uncertainty itself* a labelable, testable ground truth.

---

## 28.1 Design Principles

| ID | Principle |
|----|-----------|
| BP-1 | **Ground truth must be earned, not asserted.** A claim enters the benchmark only if its resolution meets a defined evidentiary bar (28.4) — or if it is verifiably undecidable. |
| BP-2 | **Uncertainty is a valid label.** "Insufficient/Mixed" is a correct answer to be tested, not a gap to be filled. |
| BP-3 | **Bias is measured by construction.** Matched opposing-framing pairs (28.5) are built in so skew is detectable, not hoped against. |
| BP-4 | **The benchmark is adversarial.** It deliberately contains poisoned, injected, and ambiguous-by-design items (28.7). |
| BP-5 | **Contamination is assumed.** Held-out and rotating partitions protect against model/training leakage (28.8). |
| BP-6 | **The benchmark is a living instrument.** Claims are versioned, resolutions can change, items are retired (28.9). |
| BP-7 | **The benchmark itself is governed against capture** (28.11). |

---

## 28.2 Composition & Stratification

The benchmark is stratified so that aggregate metrics cannot hide localized failure (e.g., good overall calibration masking severe bias on casualty claims).

### 28.2.1 Strata (every item tagged on all axes)

**By claim type** (from the L0 taxonomy):
- Empirical (verifiable fact)
- Legal (classification requiring a tribunal — see handling in 28.6)
- Definitional (turns on contested terms)
- Predictive
- Normative

**By difficulty:**
- *Trivial* — verifiable beyond reasonable dispute (anti-evasiveness control)
- *Tractable* — resolvable with effort
- *Hard* — resolvable but contested
- *Undecidable-by-design* — correct answer is Insufficient/Mixed

**By ground-truth resolution:**
- Confirmed-True / Confirmed-False / Mixed / Genuinely-Insufficient

**By language of primary source:** Arabic, Hebrew, English (minimum), with translated-duplicate subset for parity testing.

**By temporal class:**
- Historical-resolved (events with durable post-hoc consensus)
- Recently-resolved (resolution post-dates a cutoff — for hindsight testing, 28.7.4)
- Active-contested (used *only* in the Undecidable and Mixed strata)

**By domain anchor:**
- In-domain (Middle East)
- **Out-of-domain neutral anchor** (non-political, e.g., resolved scientific/historical/sports claims) — critical for separating *methodology error* from *domain bias*.

### 28.2.2 Minimum quotas (v1)

| Stratum | Min count |
|---------|-----------|
| Total labeled claims | >= 300 (v1 gate G0.1); target >= 1,000 by L2 |
| Per claim type | >= 40 |
| Undecidable-by-design | >= 15% of total |
| Trivial controls | >= 10% of total |
| Matched opposing-framing pairs | >= 50 pairs |
| Out-of-domain neutral anchors | >= 15% of total |
| Adversarial (poison/injection) | >= 10% of total |
| Per source language | >= 50 |

No single event or actor may account for >10% of items (prevents topical skew).

---

## 28.3 Label Schema

Each benchmark item carries:

```
item_id
claim_text (normalized)
claim_type
source_language
difficulty_class
temporal_class
domain_anchor
ground_truth_verdict         # Verified | Likely True | Mixed | Insufficient | Likely False | False
ground_truth_confidence_band # Low | Medium | High  (NOT a point estimate)
resolution_basis             # the evidentiary basis (28.4) — REQUIRED
resolution_sources[]         # pointers; access notes for paywalled/restricted
resolution_date              # when ground truth was established (bitemporal)
expert_labels[]              # individual labels pre-adjudication
irr_score                    # kappa for this item's labels
rationale                    # why this resolution, written by adjudicator
known_caveats                # honest limits on the resolution
framing_pair_id (nullable)   # links matched opposing-framing pairs
adversarial_type (nullable)  # poison | injection | laundering | ambiguous
partition                    # train-visible | held-out | rotating | sealed
version
```

`ground_truth_confidence_band` is deliberately a **band, not a number** — the benchmark must not itself manufacture false precision, and calibration is measured against the band (28.10).

---

## 28.4 Ground-Truth Resolution Standard (the hard problem)

A claim's `ground_truth_verdict` is admissible **only** if its `resolution_basis` is one of the following durable, independent bars. This is the heart of the spec.

**Tier A — Definitive resolution (eligible for Verified/False):**
- Adjudicated by a court or formal commission of inquiry with published findings
- Forensically confirmed (verified satellite/forensic/physical evidence with chain of custody)
- Formally retracted/corrected by the originating source (for False)
- Multiple (>= 3) independent primary sources with no shared origin (independence verified by graph) in agreement

**Tier B — Strong resolution (eligible for Likely True/Likely False):**
- Durable academic consensus across ideologically diverse scholarship
- >= 2 independent Tier-1 primary sources agreeing, with no credible contradicting primary source

**Tier C — Mixed:** Credible independent evidence exists on *both* sides at primary-source level, with no Tier-A resolution.

**Tier D — Genuinely-Insufficient:** No evidence meets Tier B on either side. This is a *positive* classification requiring the adjudicator to document the search performed (so "insufficient" means "we looked rigorously," not "we didn't try").

**Hard exclusions:**
- No claim is admitted on the basis of a single source, regardless of that source's tier.
- No *active-contested* empirical claim is admitted as Confirmed-True/False — it must be Mixed or Undecidable, or excluded until resolved.
- Resolution sources must be **disjoint from the platform's own operational source weighting** where possible, to avoid circularity (the benchmark must not grade the platform using the platform's own assumptions).

---

## 28.5 Matched Opposing-Framing Pairs (bias instrumentation)

The single most important bias control. For >= 50 claim cores, construct **two framings of the same underlying factual question**, each phrased sympathetically to an opposing narrative, with **identical ground truth**.

Example structure (illustrative):
- Framing alpha: "[Actor X] did [event] to [Target Y]."
- Framing beta: "[Target Y] suffered [event]; was [Actor X] responsible?"

Both must resolve to the **same** `ground_truth_verdict` and `confidence_band`. The platform's outputs on alpha vs. beta are compared:

> **Bias delta** = |confidence(alpha) - confidence(beta)| and verdict-label agreement.

Gate G1.2 requires mean delta <= 0.05 and verdict-label match >= 95% across pairs. Persistent asymmetry on a stratum localizes the bias (e.g., "we systematically express higher confidence when Actor X is the subject").

Framings must be authored by **opposing-perspective reviewers jointly** to prevent the framing set itself from being skewed (28.6).

---

## 28.6 Labeling Protocol

**Labelers:** Domain experts from the reviewer pool (historians, journalists, OSINT, regional/legal specialists), explicitly recruited for **perspective diversity** — including experts likely to disagree with each other.

**Per item:** >= 3 independent labels (>= 5 for Hard and Legal items), drawn from a panel balanced across perspectives so no item is labeled by a single ideological bloc.

**Blinding:**
- Labelers do not see each other's labels or the platform's output.
- Labelers do not see the claim's *provenance/source* during initial verdict labeling where feasible (reduces source-prestige bias) — source is revealed only in the evidence-assessment phase.
- For matched pairs, no labeler sees both framings of the same core.

**Legal/normative claims:** Labelers do **not** render the legal conclusion. They label *what authoritative bodies have concluded* and the evidentiary state. The platform is graded on faithfully mapping the legal landscape, never on declaring guilt.

**Adjudication of disagreement:**
- Compute per-item IRR. Items with kappa below threshold do **not** get a forced majority verdict — they are either (a) reclassified as Mixed/Undecidable (often the *correct* outcome and a valuable benchmark item), (b) escalated to a senior diverse panel with written adjudication, or (c) excluded with reason logged.
- **Disagreement is data:** a curated subset of high-disagreement items becomes the "ambiguous" test set (28.7.3).

**Labeler calibration & audit:** Each labeler carries a track record; systematic divergence from adjudicated outcomes is monitored (a labeler always pulling one direction is a bias signal). Labelers are compensated (budget line item).

---

## 28.7 Adversarial & Control Subsets

### 28.7.1 Poisoning set
Claims accompanied by deliberately fabricated "primary documents," sockpuppet corroboration, and citation-laundering chains (a Tier-4 rumor laundered up to Tier-2). Tests whether independence-detection and source weighting resist manufactured corroboration. Gate G1.5 / G2.5.

### 28.7.2 Prompt-injection set
Source content (PDFs, web pages, transcripts) containing embedded instructions attempting to manipulate extraction/classification LLMs. Ground truth = the *correct* extraction, ignoring the injected instruction. Tests the prompt-injection defense.

### 28.7.3 Ambiguous-by-design set
High-IRR-disagreement and genuinely-Mixed claims. Correct answer is Mixed/Insufficient. Tests against the platform's tendency to **force a conclusion** (the system must never force a conclusion). A platform that confidently resolves these *fails*.

### 28.7.4 Hindsight / temporal-holdout set
Claims resolved *after* a cutoff date. The platform is given only pre-cutoff evidence and must produce the appropriate (often Insufficient) verdict — then is checked for whether it later updates correctly when post-cutoff evidence is admitted (tests Principle 5 and INV-3 temporal integrity).

### 28.7.5 Trivial controls (anti-evasiveness)
Beyond-dispute claims. The platform must express *high* confidence here. A system that hedges on the trivially verifiable to appear "balanced" fails — this guards against the failure mode where "confidence is never 100%" degrades into uselessness.

### 28.7.6 Negative/neutral controls
Out-of-domain resolved claims (28.2.1). Large calibration gaps between neutral anchors and in-domain claims localize *domain bias* vs. *general methodology error*.

---

## 28.8 Contamination & Leakage Control

- **Partitions:** `train-visible` (may inform prompt/methodology development), `held-out` (never seen during development; used for gates), `sealed` (third-party-audit-only, never touched internally), and `rotating` (refreshed each measurement window to detect overfitting/memorization).
- **Canary items:** unique fingerprinted claims to detect if the benchmark has leaked into a model's training data (drift in canary performance signals contamination).
- **No held-out item is ever used twice for a gate decision** without rotation.
- Benchmark content is access-controlled; only aggregate metrics are published, not the held-out items themselves (publishing them would burn them).

---

## 28.9 Versioning & Maintenance

- Benchmark is **bitemporal**: every item and every resolution is versioned with `resolution_date`.
- **Resolutions can change.** When new Tier-A/B evidence emerges, an item's ground truth is updated *as a logged event*; the prior version is retained so historical platform performance remains reproducible (INV-2/INV-3).
- **Retirement:** items whose claims become trivially settled or stale are moved out of active gating into an archive.
- **Growth target:** >= 300 (G0.1) -> >= 1,000 by L2 -> continuous per-domain expansion (each new region/domain builds its own benchmark before public exposure, per Section 23.7 G4.1).
- Each benchmark version is published with a changelog (consistent with Section 20 transparency).

---

## 28.10 Metrics Computed From the Benchmark

| Metric | Definition | Gate(s) |
|--------|------------|---------|
| **ECE (calibration)** | Expected Calibration Error: do "High-band" verdicts resolve correctly at the high-band rate? | G1.1, G2.1, G3.1 |
| **Bias delta** | Mean confidence/verdict divergence across matched framing pairs | G1.2 |
| **Classification kappa** | Agreement of evidence classification with expert panel | G1.3 |
| **Citation accuracy** | Fraction of citations that actually support the cited statement | G0.4 |
| **Extraction P/R** | Claim/entity extraction precision/recall | G0.3 |
| **Undecidability recall** | Correct Mixed/Insufficient assignment on 28.7.3 | G1.6 |
| **Poison/injection resistance** | Verdict-flip rate under 28.7.1/28.7.2 | G1.5, G2.5 |
| **Hindsight correctness** | Correct pre-cutoff verdict + correct post-cutoff update | INV-3 (temporal integrity) |
| **Language parity** | Verdict divergence on translated duplicates | G0.6 |
| **Anchor gap** | Calibration delta between neutral anchors and in-domain | bias diagnostic |

These definitions are the canonical source for Section 26 (Success Metrics).

---

## 28.11 Governance of the Benchmark

The benchmark can be captured to make a biased platform *look* unbiased. Controls:

- **Benchmark Committee** distinct from the engineering team and balanced for perspective diversity (no single national/ideological bloc holds a majority).
- **Sealed third-party partition** (28.8) audited by an external body; the platform team never sees it.
- **Open methodology, controlled content:** the *construction methodology, strata quotas, and resolution standard* are public; the held-out/sealed *items* are not.
- **Change control:** additions, resolution changes, and quota changes are logged events with rationale, reviewed by the committee.
- **Conflict-of-interest disclosure** for all labelers and committee members.
- **Adversarial review:** opposing-perspective experts periodically attempt to demonstrate the benchmark is skewed; their findings are published (analogous to the platform's own bias audits).

---

## 28.12 Additional Improvements Toward the End Goal

Beyond the benchmark itself, three things make the benchmark *worth* having:

1. **Public "calibration ledger."** Continuously publish, for resolved-after-the-fact claims, what the platform said vs. what turned out true. This is the most powerful trust artifact the platform can produce — it converts "trust our method" into a verifiable track record, and it's only possible because the benchmark/temporal model exist.
2. **External benchmark contribution.** Let vetted academic partners submit candidate claims + resolutions (under the 28.4 standard). This both grows the set and distributes credibility — outsiders helped build the ruler.
3. **Shared/open standard.** Long-term (L5), publish the benchmark *methodology* as an open standard for evidence-platform evaluation. Becoming the institution that defines how these systems are measured is a stronger moat than any single verdict, and aligns with Section 27's "global standard" vision.

---

# 25. Budget Estimates (Revised)

The base v1.0 estimate (\$1.3M–2.5M/yr) omitted several load-bearing costs the
review flagged: data/content licensing, legal & insurance, certifications, reviewer/
labeler compensation, translation, and independent audits. Revised below. Figures
are Year-1 USD ranges for a Stage L0→L2 build (see Section 23); they are planning
figures, not commitments.

## 25.1 Line items

| Category | Year-1 range | Notes |
|----------|--------------|-------|
| **Engineering** | \$900k–1.6M | 5–8 ICs (AI/ML, backend, data, DevOps) + fractional lead. The dominant cost. |
| **Research & review** | \$350k–700k | Historians, journalists, OSINT; **includes paid reviewer/labeler time** (gold benchmark §28.6 + escalation queue FR-007) — previously unbudgeted. |
| **Data & content acquisition** | \$80k–250k | Paywalled archives/journals, news licensing, **satellite imagery** + forensic/geolocation tooling, court-record access. Recurring. |
| **Translation & multilingual** | \$40k–120k | Arabic/Hebrew/English from day one (Section 23 L0) — human translation/QA, not just MT. |
| **Infrastructure** | \$75k–150k | Neo4j/Qdrant/Postgres/object storage, compute, LLM API spend. |
| **Security & compliance** | \$120k–300k | SOC2 Type II + ISO27001 (6–18 mo, audit fees + tooling + staff time), pen-tests. |
| **Legal & insurance** | \$120k–350k | Defamation/media-liability counsel + **libel insurance** (Section 29), privacy counsel, jurisdiction review, takedown handling. |
| **Independent audits** | \$40k–100k | Third-party **bias audits** (≥2/yr, Section 23 gates G2.2/G3.2) + benchmark governance (28.11). |
| **Operations & governance** | \$100k–200k | Board/advisory ops, nonprofit admin, accounting, comms. |
| **Contingency (~15%)** | \$280k–550k | Hard-to-reverse domain; budget for surprises. |
| **Estimated Year-1 total** | **\$2.2M–4.3M** | Up from the v1.0 \$1.3M–2.5M once omitted costs are included. |

## 25.2 Funding-independence note
Per Section 19/20, **funding transparency is a budget concern, not only a governance
one**: donation caps, a published donor list, and a funder↔verdict firewall are
prerequisites for credibility on this topic and should be costed into Operations &
Governance (legal structuring, disclosure tooling).

---

# 29. Legal & Liability

Publishing "Likely False" / "False" about identifiable people and organizations on
the world's most contested topic is the platform's highest *operational* risk. This
section is a posture, not legal advice; engage qualified counsel per jurisdiction
before any public verdict (a Stage L1→L2 precondition, Section 23.4).

## 29.1 Core stance: evidence, not legal guilt
The platform assesses **evidentiary support for empirical claims**; it does **not**
adjudicate legal guilt or render legal conclusions. Legal/definitional/normative
claims are typed as such (claim-type taxonomy, Section 23 L0) and are handled by
**mapping what authoritative bodies have concluded**, never by the platform declaring
a verdict of its own. Every published verdict carries this framing explicitly.

## 29.2 Defamation / libel exposure
- **Truth + opinion + privilege** are the standard defenses; the platform's design
  supports them: every verdict is fully **traceable to evidence** (INV-TRACE),
  **reproducible** (INV-REPRO), and **explainable** — i.e. a documented, good-faith,
  methodologically-grounded assessment rather than an assertion of fact about a person.
- **Confidence framing matters legally**: bands + "the evidence currently supports…"
  language (never bare "X is false") keep statements in protected opinion/assessment
  territory. "Insufficient/Mixed" are first-class outcomes (INV-FORCE).
- **Jurisdiction strategy**: libel law varies enormously (US Sullivan-style actual-
  malice vs. claimant-friendly regimes elsewhere). Decide hosting/incorporation and
  a geo-exposure posture *before* L2; consider geo-fencing high-risk verdicts pending
  review.

## 29.3 Correction & retraction policy
- Errors are corrected **fast and visibly**, within the **≤72h SLA (INV-6)**.
- Corrections are **append-only verdict versions**, not silent edits — the
  bitemporal store (ADR-0008) preserves "what we said and when, and why it changed,"
  which is both a trust artifact and a legal-defensibility artifact.
- A public **correction log** + the **calibration ledger** (28.12) demonstrate
  good-faith, systematic error handling.

## 29.4 Takedowns, appeals, and right-of-reply
- Named subjects get a **right of reply** and a first-class **appeals path**
  (FR-021): new evidence, source challenge, methodology concern — all logged publicly.
- A documented **takedown/dispute intake** routes legal complaints to counsel +
  the review committee; frivolous vs. meritorious are triaged, not auto-actioned.

## 29.5 Source & subject protection (do-no-harm)
- Verdicts on active-conflict claims can endanger **witnesses, sources, and
  bystanders**. A do-no-harm review gates publication of anything that could expose
  at-risk individuals; eyewitness/whistleblower identities are protected and
  segregated from public evidence.

## 29.6 Privacy & the immutability↔erasure tension
- **GDPR/CCPA** rights (incl. erasure) conflict naïvely with immutable audit logs.
  Resolution (ARCHITECTURE.md §2): **immutably log decisions + public evidence**,
  keep **personal data segregated and erasable** (crypto-shredding), so the audit
  trail of *the assessment* survives while *personal data* can be removed.

## 29.7 Insurance
- Carry **media/defamation liability insurance** sized to the launch domain (a
  budgeted Year-1 line item, §25). Bind coverage **before** the first public verdict.

---

# 30. Platform Threat Model

The Influence Operations module (base §18) points outward; this section points the
same adversarial lens **inward** — the platform itself is a high-value target. Each
threat lists its status: ✅ a control exists in code, ◐ partially addressed, ○ planned.

## 30.1 Evidence poisoning & manufactured corroboration
- **Threat:** flooding sources, fabricated "primary documents," sockpuppet outlets
  citing each other to fake independent corroboration; citation laundering (a Tier-4
  rumor laundered up to a Tier-2 citation).
- **Controls:** ✅ **independence analysis** groups sources into provenance clusters
  so shared-origin / citation-cycle corroboration is detected and down-weights the
  score (`independence_ratio`, ADR-0007, wired into the Trust Engine). ◐ source-tier
  weighting and corroboration over *distinct provenance*, not raw count. ○ graph-based
  source-ownership detection; ○ rate-limited, reputation-gated submissions.

## 30.2 Prompt injection via ingested content
- **Threat:** URLs/PDFs/social posts carrying embedded instructions that try to
  steer extraction/classification LLMs.
- **Controls:** ✅ untrusted source text is passed as **user content, never as
  instructions**, through the recorded LLM wrapper (ADR-0005); ✅ the adversarial
  **prompt-injection benchmark subset** (28.7.2) gates progression; ◐ output schema
  validation rejects malformed/manipulated extractions.

## 30.3 Scoring manipulation
- **Threat:** getting an LLM to inflate/deflate a score or verdict.
- **Controls:** ✅ **LLMs never score** — confidence/verdicts come only from the
  deterministic Trust Engine (INV-DETERMINISM, ADR-0003), so there is no LLM path to
  a score to attack; ✅ scoring is reproducible from versioned config.

## 30.4 Resource exhaustion / DoS on scarce humans
- **Threat:** submission flooding and **appeal abuse** to exhaust the human review
  queue (the platform's scarcest resource).
- **Controls:** ◐ gateway is the single choke point for rate-limiting/abuse gating
  (Section 23 G2.x); ○ per-actor reputation + submission quotas; ○ escalation-volume
  vs. reviewer-throughput monitoring (gate G2.6).

## 30.5 Source-reliability & methodology gaming
- **Threat:** gaming source-reliability scores over time; lobbying to change weights.
- **Controls:** ✅ weights/source-reliability are **versioned config** with every
  verdict recording its config version; ○ change-control + public comment on weight
  changes (Section 20); ○ anomaly detection on reliability drift.

## 30.6 Benchmark capture
- **Threat:** capturing the gold benchmark to make a biased platform *look* unbiased.
- **Controls:** ◐ benchmark governance (28.11) — perspective-diverse committee,
  sealed third-party partition, open methodology/closed items; ○ contamination
  canaries (28.8); ○ adversarial review.

## 30.7 Model & supply-chain integrity
- **Threat:** a silent model upgrade changing historical verdicts; dependency
  compromise.
- **Controls:** ✅ **pinned, recorded model IDs** per call (INV-REPRO) so verdicts
  are reproducible and upgrades are explicit; ◐ committed lockfiles + codegen-drift
  CI; ○ SBOM + signed dependencies; ○ curated internal package index.

## 30.8 Firewall integrity (coordination ↔ truth)
- **Threat:** influence/coordination signals leaking into truth scoring (or vice
  versa), letting "this looks coordinated" silently lower a true claim's score.
- **Controls:** ✅ **one-way isolation** required in code (INV-INDEPENDENCE);
  ○ an audit asserting zero scoring leakage from the Influence-Ops module (gate G4.2).

## 30.9 Summary
The architecture's defining choices — deterministic scoring, the recorded LLM
boundary, graph-based independence, bitemporal reproducibility — are not only quality
features; they are **the threat model's primary mitigations**. The open (○) items
above are the prioritized security backlog.
