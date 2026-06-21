# 0010. Canonical record ownership: Postgres canonical, Neo4j projection

- **Status:** Accepted
- **Date:** 2026-06-21
- **Deciders:** Project lead
- **Related:** [0006](0006-retrieval-seams.md), [0007](0007-independence-citation-laundering.md), [0008](0008-bitemporal-verdict-store.md); CLAUDE.md §3 (INV-TRACE, INV-TEMPORAL); ARCHITECTURE.md §2, §7, §8

## Context
Claim and verdict records must have one authoritative home with a clear consistency
model: bitemporal, append-only, transactional, and re-derivable (INV-TEMPORAL,
INV-TRACE). Separately, the platform needs graph traversal — citation/provenance
chains for independence analysis (ADR-0007) and evidence relationships for retrieval
(ADR-0006). A graph database (Neo4j) is good at traversal but a poor system of record
for versioned, transactional truth; a relational store (Postgres) is the opposite.
Picking one store for both would compromise either correctness or traversal.

## Decision
**Postgres is the canonical system of record; Neo4j is a derived projection.** The
bitemporal `VerdictStore` (ADR-0008) and the config/audit/review stores persist to
Postgres via SQLAlchemy — that is the source of truth for claims, verdicts, config
versions, and the audit log. Neo4j holds a **projection** built from those records
(plus ingested citation edges) purely to serve traversal: provenance grouping for
`independence_ratio` and graph-based retrieval. The projection is rebuildable from
Postgres and never the authority for a verdict. Qdrant is likewise a derived index
(embeddings), not a record store.

## Consequences
- One transactional, append-only authority for truth; "as-of" history and audit live
  where ACID guarantees hold (INV-TEMPORAL, INV-TRACE).
- Neo4j/Qdrant can be wiped and rebuilt from Postgres without data loss — they are
  caches/projections, which simplifies disaster recovery and schema evolution.
- Cost: a projection/sync path must be maintained (graph seeding from canonical
  records is tracked as backlog). Until it exists, citation edges are supplied
  explicitly (e.g. `/v1/assess` `citations`, ADR-0007) rather than read from a live
  graph.
- Independence stays one-way: graph data feeds scoring as an input override, never
  the reverse (INV-DETERMINISM boundary preserved).

## Alternatives considered
- **Neo4j canonical** — weak transactional/bitemporal story for versioned truth;
  re-deriving "what did we conclude on date X" becomes bespoke. Rejected.
- **Single Postgres store, no graph** — traversal queries (multi-hop provenance,
  citation cycles) become awkward and slow in SQL. Kept the graph as a projection.
- **Event-sourced log as the authority** — more machinery than needed now; the
  append-only `VerdictStore` already gives the essential event-log properties.
