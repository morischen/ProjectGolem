# 0006. Retrieval seams (Embedder / VectorStore / GraphStore)

- **Status:** Accepted
- **Date:** 2026-06-19
- **Deciders:** Project lead
- **Related:** [ARCHITECTURE.md](../../ARCHITECTURE.md) §4.3; [ai-services/evidence-engine](../../ai-services/evidence-engine/); review §4 (independence/citation-laundering)

## Context
The Evidence Retrieval Engine shipped with a `Retriever` protocol and a
`StubRetriever`. Real retrieval needs the data stores (Qdrant for semantic search,
Neo4j for graph traversal), but: (a) CI/tests must stay hermetic — no live DB, no
network, no API keys; (b) we want to swap or compose backends without touching the
classification/gather logic; (c) embeddings come from a model we haven't chosen yet.

## Decision
Introduce narrow seams, each a `Protocol` with a real adapter and a test fake:
- **`Embedder`** — `embed(text) -> list[float]`. `StubEmbedder` is deterministic and
  dependency-free for tests; real embedders implement the same protocol later.
- **`VectorStore`** — `search(vector, limit) -> list[VectorHit]`. `QdrantVectorStore`
  adapts the `qdrant-client`; a fake store is used in tests.
- **`GraphStore`** (P2) — Neo4j-backed candidate/independence queries.

Concrete retrievers (`SemanticRetriever`, later `GraphRetriever`, `CompositeRetriever`)
are built on these seams and implement the existing `Retriever` protocol, so
`gather()` consumes them unchanged. Tests inject fakes; real adapters are validated
against `infra/docker-compose.yml` (Qdrant/Neo4j), not in CI.

## Consequences
- Retrieval logic is unit-testable with no infrastructure; the SDK-touching code is
  isolated in thin adapters (and small `make_*` factories that import the SDK).
- Backends are swappable/composable behind one protocol; the embedding model is a
  deferred, isolated choice.
- A genuine integration gap remains: adapters are exercised against live stores only
  when a developer runs docker-compose. CI proves wiring + mapping, not the DB round-trip.

## Alternatives considered
- **Import qdrant/neo4j SDKs directly in the retriever** — couples logic to clients,
  breaks hermetic tests. Rejected.
- **Defer all retrieval until infra is provisioned** — leaves the pipeline's middle
  permanently stubbed. Rejected; build against seams now.
