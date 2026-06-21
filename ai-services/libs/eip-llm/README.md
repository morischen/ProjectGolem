# eip-llm

Shared **recorded LLM wrapper** ([ADR-0005](../../../docs/adr/0005-llm-recorded-wrapper.md),
[ADR-0009](../../../docs/adr/0009-openrouter-multi-model.md)). Every call returns a
`RecordedCall` (model id + prompt + inputs + output) for reproducibility (INV-REPRO).
The wrapper does language work only — it never scores (INV-DETERMINISM).

## Clients (one `LLMClient` protocol)
- `StubLLMClient` — deterministic, network-free; the default in tests.
- `OpenRouterLLMClient` — **multi-model via OpenRouter** (OpenAI-compatible). One key,
  many models; `model_id` is an OpenRouter slug.
- `AnthropicLLMClient` — Claude direct via the Anthropic SDK.

## Provider selection
`build_llm_from_env()` picks the runtime provider:

| Env | Result |
|-----|--------|
| `OPENROUTER_API_KEY` set | `OpenRouterLLMClient(OPENROUTER_MODEL)` — default `anthropic/claude-opus-4.8` |
| else | `AnthropicLLMClient` (needs `ANTHROPIC_API_KEY`) |

Optional: `OPENROUTER_SITE_URL` / `OPENROUTER_APP_NAME` for OpenRouter attribution.
Set `OPENROUTER_MODEL` to any slug from openrouter.ai/models (e.g. `openai/gpt-5`,
`google/gemini-2.5-pro`). claim-engine and evidence-engine default to this selector.

## Develop & test
```bash
uv sync && make qa     # hermetic — OpenRouter/Anthropic clients are tested with fakes
```
