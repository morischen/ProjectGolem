# 0011. Embedding model and chunking strategy for semantic retrieval

- **Status:** Proposed
- **Date:** 2026-06-21
- **Deciders:** Project lead
- **Related:** [0006](0006-retrieval-seams.md), [0010](0010-canonical-record-ownership.md), [0012](0012-multilingual-pipeline.md); ARCHITECTURE.md §8; blueprint §23 (L0 multilingual)

## Context
Semantic retrieval over Qdrant needs an embedding model and a chunking strategy. Two
forces shape the choice: (1) the domain is **multilingual from day one** —
Arabic/Hebrew/English (ADR-0012, blueprint §23 L0) — so an English-only embedder
would silently degrade non-English recall; (2) evidence is source documents of
varying length, and retrieval quality depends on chunk granularity. The retrieval
seam (ADR-0006) already abstracts an `Embedder`, so the concrete model is swappable
without touching call sites — but we still need a default and a chunking rule.

## Decision
Embed behind the ADR-0006 `Embedder` seam with a **multilingual sentence-embedding
model** (BGE-M3 / multilingual-E5 class) as the default, so Arabic/Hebrew/English map
into one shared vector space and cross-lingual retrieval works. **Chunk by passage**
(~256–512 tokens) with ~15% overlap, splitting on sentence/paragraph boundaries; one
vector per chunk, each carrying `source_id`, language, and char offsets back to the
canonical record (INV-TRACE). The embedding model id and revision are pinned and
recorded alongside vectors (INV-REPRO), so re-embedding on a model change is a
deliberate, versioned migration. The vector index is a **projection** (ADR-0010),
rebuildable from canonical sources.

## Consequences
- Cross-lingual recall without per-language indexes; aligns with ADR-0012.
- Pinning + recording the model means embeddings are reproducible and a model upgrade
  is an explicit re-index, not silent drift.
- Cost: a real embedder + ingestion/chunking pipeline is still to be built (backlog);
  until then the seam is exercised with stub/local embedders in hermetic tests.
- Chunk-to-source offsets keep every retrieved passage traceable to its origin.

## Alternatives considered
- **English-only embedder + translate-then-embed** — adds a translation dependency in
  the hot path and loses nuance in the original language; multilingual embedder is
  simpler and keeps originals authoritative. Reconsider if quality demands it.
- **Whole-document embedding (no chunking)** — poor retrieval precision and dilutes
  long documents. Rejected.
- **Per-language vector collections** — fragments the index and complicates
  cross-lingual corroboration. Rejected in favor of one shared space.
