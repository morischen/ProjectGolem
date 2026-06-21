# 0009. LLM access via OpenRouter (multi-model)

- **Status:** Accepted
- **Date:** 2026-06-21
- **Deciders:** Project lead
- **Related:** [ADR-0005](0005-llm-recorded-wrapper.md) (recorded wrapper), [ADR-0002](0002-polyglot-python-ai-typescript-web.md) (Anthropic default), [ADR-0003](0003-deterministic-trust-engine.md) (LLMs never score)

## Context
ADR-0005 standardized LLM access behind a recorded wrapper with the Anthropic SDK as
the default provider. We now want to use **multiple models** (cross-model evaluation,
cost/availability flexibility, per-task model choice) without integrating each
vendor SDK separately. OpenRouter exposes many models (Anthropic, OpenAI, Google,
open models) through a single **OpenAI-compatible** API and one credential.

## Decision
Add `OpenRouterLLMClient` to the shared `eip-llm` wrapper, implemented against the
OpenAI-compatible Chat Completions API (`base_url=https://openrouter.ai/api/v1`,
`OPENROUTER_API_KEY`). `model_id` is an OpenRouter slug
(e.g. `anthropic/claude-opus-4.8`, `openai/gpt-5`), configured via `OPENROUTER_MODEL`.
`build_llm_from_env()` is the single selection point: **OpenRouter when
`OPENROUTER_API_KEY` is set, else Anthropic direct**; services default to it.

It remains a `RecordedCall`-returning `LLMClient` — the `model_id` recorded now
includes the provider/model slug, so reproducibility (INV-REPRO) survives model
switches. The OpenAI-compatible client is built lazily and is injectable, so the
adapter is unit-tested with a fake (no key/network); the determinism firewall
(LLMs never score, ADR-0003) and the prompt-injection boundary are unchanged.

## Consequences
- One credential, many models; model choice is an env var, not a code change.
- Reproducibility is preserved and arguably improved (provider+slug captured per call).
- New dependency (`openai` SDK) used only as the OpenRouter transport.
- A vendor sits in the request path (OpenRouter); availability/pricing/routing are
  now its concern. The Anthropic-direct client is retained as a fallback/escape hatch.
- This **revises ADR-0002's "Anthropic default"**: the default runtime provider is
  now OpenRouter when configured. ADR-0005's recorded-wrapper contract is unchanged.

## Alternatives considered
- **Per-vendor SDKs behind the wrapper** — N integrations, N auth schemes; more code,
  slower to add a model. Rejected for now (OpenRouter covers the breadth).
- **Anthropic-only** — simplest, but single-model; doesn't meet the multi-model goal.
