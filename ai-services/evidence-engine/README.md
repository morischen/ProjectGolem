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
