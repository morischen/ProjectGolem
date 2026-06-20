# 0007. Independence / citation-laundering detection

- **Status:** Accepted
- **Date:** 2026-06-19
- **Deciders:** Project lead
- **Related:** review §4 (platform threat model); [ADR-0006](0006-retrieval-seams.md); base blueprint §10 (Independence component), §13 (GraphRAG)

## Context
Corroboration is a core confidence signal, but it is attackable: an adversary (or
ordinary citation chains) can make one source look like many — N outlets all
repeating a single origin, or citation cycles (A cites B cites A). Counting those as
N independent confirmations inflates confidence. The review flagged this as a primary
reason the GraphRAG architecture earns its keep: independence is a graph property,
not a per-document one.

## Decision
Compute independence by grouping sources into **provenance clusters** — the
weakly-connected components of the citation graph (an edge `a → b` means `a` cites /
derives from `b`). Sources in the same cluster count as **one** independent voice.
`assess_independence(source_ids, citations)` returns an `IndependenceReport`
(distinct sources, independent groups, `independence_ratio = groups / sources`, and
the cluster membership). The analysis is a **pure, deterministic function**; citation
edges are supplied by the knowledge graph (Neo4j) at runtime but are not required to
test it.

## Consequences
- Laundered corroboration is detectable and quantifiable (`independence_ratio` < 1).
- This naturally feeds the Trust Engine's Independence component later — distinct
  *provenance clusters* should drive the score, not raw source count.
- It is the clearest justification for the graph store: this signal can't be derived
  from document similarity alone.
- Quality depends on the citation edges the graph actually captures — missing edges
  understate laundering. Edge extraction is its own future work.

## Alternatives considered
- **Count distinct `source_id`s** — the status quo in the Trust Engine; trivially
  fooled by sockpuppets/syndication. Kept as a floor, superseded by clusters.
- **Heuristics on source names/domains** — brittle and gameable; the provenance
  graph is the principled signal.
