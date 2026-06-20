# 0005. LLM access via a recorded wrapper

- **Status:** Accepted
- **Date:** 2026-06-19
- **Deciders:** Project lead
- **Related:** [ADR-0003](0003-deterministic-trust-engine.md); CLAUDE.md §3 (INV-REPRO, INV-DETERMINISM); [ai-services/claim-engine/](../../ai-services/claim-engine/)

## Context
LLM-assisted steps (claim extraction, entity/event recognition, claim-type
classification, explanations) are non-deterministic and not directly auditable. The
platform requires that every LLM-assisted output be reproducible (INV-REPRO) and
that scoring never originate in an LLM (INV-DETERMINISM, ADR-0003). Scattering raw
SDK calls across services would make both guarantees impossible to enforce.

## Decision
All LLM access goes through a single recorded-wrapper interface (`LLMClient`) whose
every call returns a `RecordedCall` capturing `{model_id, system, prompt, inputs,
output}`. Two implementations:
- `AnthropicLLMClient` — the real client (Claude Opus 4.8, adaptive thinking) via
  the official `anthropic` SDK. Default provider is Anthropic (ADR-0002).
- `StubLLMClient` — deterministic, network-free; the default in tests and smoke so
  CI stays hermetic.

The wrapper is used only for language tasks. It is structurally impossible to route
a confidence score or verdict through it — those come from the deterministic Trust
Engine. Untrusted source text is passed as the user prompt, never as instructions
(prompt-injection boundary).

## Consequences
- Every LLM output carries the metadata needed to re-derive it; logs/audits can
  store the `RecordedCall`.
- Tests never hit the network or need an API key — they inject `StubLLMClient`.
- Swapping models/providers is a one-place change; the recorded `model_id` keeps
  historical outputs traceable to the exact model.
- A small indirection cost over calling the SDK directly — accepted for the
  auditability guarantee.

## Alternatives considered
- **Direct SDK calls per service** — no uniform reproducibility record; easy to
  accidentally leak scoring into an LLM call. Rejected.
- **Mocking the SDK in tests instead of a stub client** — couples tests to SDK
  internals and is brittle across SDK versions. The stub is a stable seam.
