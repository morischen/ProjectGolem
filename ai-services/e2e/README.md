# e2e

Cross-engine end-to-end integration tests. Imports all three Python engines (via
uv path dependencies) and drives the full pipeline in one process:

**claim → evidence → trust** (extract → gather+classify → score)

Evidence crosses package boundaries as JSON — the same boundary it crosses over
HTTP — so these tests prove the independently-generated contracts in each service
actually line up (e.g. `EvidenceRelation` values match; an evidence-engine
`Evidence` re-validates as a trust-engine `Evidence`). LLM and retriever are
stubbed, so the suite is hermetic and deterministic.

```bash
uv sync
make qa     # lint + test
```

This is a non-package project (`[tool.uv] package = false`) — tests only.
