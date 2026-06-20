# Evidence Retrieval Engine

The middle of the pipeline: given a claim, retrieve candidate sources and classify
each one's relation to the claim (Supports / Contradicts / Neutral / Inconclusive),
emitting `Evidence` (contracts/evidence.schema.json) ready for the Trust Engine.

- **Retrieval** is a seam (`Retriever`): `StubRetriever` for tests; real
  multi-source/graph/vector retrievers implement the same protocol later.
- **Classification** is LLM work via the recorded wrapper ([ADR-0005](../../docs/adr/0005-llm-recorded-wrapper.md)).
  The LLM assigns the *relation* only — it never scores truth/confidence
  (INV-DETERMINISM). quality/freshness/source_tier come from retrieval metadata.

Pipeline position: **Claim Engine → Evidence Engine → Trust Engine** (extract →
retrieve+classify → score).

## Retrieval backends (ADR-0006 / ADR-0007)
Retrievers sit behind the `Retriever` protocol and are composable:
- `SemanticRetriever` — `Embedder` + `VectorStore` (Qdrant adapter).
- `GraphRetriever` — `GraphStore` (Neo4j adapter); knowledge-graph traversal.
- `CompositeRetriever` — merges + de-dupes across backends.
- `assess_independence` — groups sources into provenance clusters to detect
  shared-origin / citation-cycle laundering (review §4).

CI is hermetic (fakes; no live DB). To run against real stores via
[infra/docker-compose.yml](../../infra/docker-compose.yml):
```bash
docker compose -f infra/docker-compose.yml up -d qdrant neo4j
# (seed a Qdrant "evidence" collection + the claim/evidence graph — not yet scripted)
QDRANT_URL=http://localhost:6333 \
NEO4J_URI=bolt://localhost:7687 NEO4J_USER=neo4j NEO4J_PASSWORD=devpassword \
  make serve   # /v1/gather will now retrieve server-side when candidates are omitted
```

## Develop & test
```bash
uv sync
make gen      # regenerate the Evidence model from ../../contracts
make qa       # lint + typecheck + test + smoke
```

## Status
First vertical: stub retriever + LLM classification → contract-valid Evidence. No
real retrieval backend or HTTP surface yet (later loops). The recorded LLM wrapper
comes from the shared `eip-llm` lib ([ai-services/libs/eip-llm](../libs/eip-llm/)),
also used by claim-engine.
