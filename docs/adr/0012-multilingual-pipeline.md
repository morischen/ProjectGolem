# 0012. Multilingual pipeline: originals authoritative, translate for processing

- **Status:** Proposed
- **Date:** 2026-06-21
- **Deciders:** Project lead
- **Related:** [0005](0005-llm-recorded-wrapper.md), [0008](0008-bitemporal-verdict-store.md), [0011](0011-embeddings-and-chunking.md); CLAUDE.md §3 (INV-TRACE, INV-REPRO); blueprint §23 (L0), §26, §28

## Context
The initial domain (Middle East conflict reporting) requires Arabic, Hebrew, and
English **from day one** (blueprint §23 L0), and success metrics demand measured
**language parity** (§26/§28) — non-English claims must not be assessed worse than
English ones. Source evidence arrives in many languages; LLM extraction/classification
quality varies by language; and INV-TRACE requires that a verdict always link back to
the evidence *as published*, not only to a translation. So we must decide where
translation sits and how a claim's working language is chosen without losing the
original.

## Decision
**The original-language text is authoritative and always retained**; translation is a
recorded, derived artifact, never a replacement. At ingestion, each source is language-
detected and stored in its original form; a translation into a canonical working
language (English) is produced and stored *alongside* it for LLM extraction and
relation classification. The original language code is carried on claims/evidence and
through embeddings (ADR-0011). Translations go through the recorded LLM/MT wrapper
(ADR-0005) so model id + input are reproducible (INV-REPRO). Verdicts and the portal
always cite the **original** passage (INV-TRACE), showing the translation as an aid.
Language parity is measured as a first-class slice of the gold benchmark — per-language
verdict accuracy and calibration (ADR via §28) — and gated like the overall metrics.

## Consequences
- One working language keeps the Trust Engine and classification logic language-
  agnostic while preserving originals for traceability and appeals.
- Parity becomes measurable and enforceable (per-language calibration slices) rather
  than assumed.
- Cost: a translation/MT step and language metadata throughout ingestion; mistrans-
  lation is a real risk, mitigated by keeping originals authoritative and surfacing
  both in the UI.
- Builds on the multilingual embedder (ADR-0011) so retrieval is cross-lingual even
  before translation.

## Alternatives considered
- **Per-language models/pipelines end to end** — maximal fidelity but triples the
  surface area and complicates parity comparison. Rejected for now.
- **Translate-and-discard originals** — violates INV-TRACE; appeals and audits need
  the source as published. Rejected.
- **English-only at launch** — fails the §23 L0 requirement and the mission. Rejected.
