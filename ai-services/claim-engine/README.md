# Claim Engine

Normalizes raw input into a `Claim` (contracts/claim.schema.json): extraction of
actors/targets/events/dates/assertions plus claim-type classification. The LLM does
language work only — it **never** assesses truth or assigns confidence
([ADR-0003](../../docs/adr/0003-deterministic-trust-engine.md)); scoring is the
Trust Engine's deterministic job.

## LLM access
All LLM calls go through a **recorded wrapper** ([ADR-0005](../../docs/adr/0005-llm-recorded-wrapper.md)):
every call returns a `RecordedCall` (model id + prompt + inputs + output) so any
result is reproducible (INV-REPRO). `StubLLMClient` is the deterministic,
network-free client used in tests; `AnthropicLLMClient` (Claude Opus 4.8, adaptive
thinking) is the real implementation, used at runtime with `ANTHROPIC_API_KEY`.

## Develop & test
```bash
uv sync
make gen      # regenerate the Claim model from ../../contracts
make qa       # lint + typecheck + test + smoke
```

## Status
First vertical: extraction + claim-type classification, validated against the Claim
contract. Not yet wired to an HTTP surface or the gateway (later loops).
