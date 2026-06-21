"""Shared recorded LLM wrapper (ADR-0005, ADR-0009).

Every LLM call returns a `RecordedCall` capturing model id + prompt + inputs +
output, so any LLM-assisted result is reproducible (INV-REPRO). The wrapper does
language work only — it never produces a score or verdict (INV-DETERMINISM).

Clients:
- `StubLLMClient` — deterministic, network-free; the default in tests/offline.
- `OpenRouterLLMClient` — multi-model via OpenRouter (OpenAI-compatible API); the
  preferred runtime provider (one key, many models). `model_id` is the OpenRouter
  slug (e.g. `anthropic/claude-opus-4.8`, `openai/gpt-5`).
- `AnthropicLLMClient` — Claude direct via the Anthropic SDK.

`build_llm_from_env()` selects the runtime provider from environment variables.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

DEFAULT_OPENROUTER_MODEL = "anthropic/claude-opus-4.8"  # override via OPENROUTER_MODEL

# OpenAI-compatible "JSON mode" — nudges the model to emit a single JSON object.
JSON_OBJECT_RESPONSE_FORMAT: dict[str, Any] = {"type": "json_object"}


@dataclass(frozen=True)
class RecordedCall:
    model_id: str
    system: str
    prompt: str
    inputs: dict[str, str]
    output: str


@runtime_checkable
class LLMClient(Protocol):
    def complete(
        self,
        *,
        system: str,
        prompt: str,
        inputs: dict[str, str],
        response_format: dict[str, Any] | None = None,
    ) -> RecordedCall: ...


class StubLLMClient:
    """Deterministic client for tests: returns preset outputs in sequence (the last
    output repeats once exhausted) and records every call. No network."""

    def __init__(self, outputs: list[str] | str, model_id: str = "stub") -> None:
        self._outputs = [outputs] if isinstance(outputs, str) else list(outputs)
        if not self._outputs:
            raise ValueError("StubLLMClient requires at least one output")
        self._index = 0
        self._model_id = model_id
        self.calls: list[RecordedCall] = []

    def complete(
        self,
        *,
        system: str,
        prompt: str,
        inputs: dict[str, str],
        response_format: dict[str, Any] | None = None,
    ) -> RecordedCall:
        output = self._outputs[min(self._index, len(self._outputs) - 1)]
        self._index += 1
        call = RecordedCall(
            model_id=self._model_id,
            system=system,
            prompt=prompt,
            inputs=dict(inputs),
            output=output,
        )
        self.calls.append(call)
        return call


class AnthropicLLMClient:
    """Real client backed by the Anthropic SDK (scaffold — not exercised in CI).
    Claude Opus 4.8, adaptive thinking. Requires `ANTHROPIC_API_KEY` at runtime."""

    def __init__(self, model_id: str = "claude-opus-4-8", max_tokens: int = 2000) -> None:
        self._model_id = model_id
        self._max_tokens = max_tokens

    def complete(
        self,
        *,
        system: str,
        prompt: str,
        inputs: dict[str, str],
        response_format: dict[str, Any] | None = None,
    ) -> RecordedCall:
        # response_format is honored by the OpenRouter client; Anthropic-direct
        # uses prompting + the tolerant parser instead.
        import anthropic

        client: Any = anthropic.Anthropic()
        message = client.messages.create(
            model=self._model_id,
            max_tokens=self._max_tokens,
            thinking={"type": "adaptive"},
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(
            getattr(block, "text", "")
            for block in message.content
            if getattr(block, "type", "") == "text"
        )
        return RecordedCall(
            model_id=self._model_id,
            system=system,
            prompt=prompt,
            inputs=dict(inputs),
            output=text,
        )


class OpenRouterLLMClient:
    """Multi-model client via OpenRouter's OpenAI-compatible API (ADR-0009).

    `model_id` is an OpenRouter slug. The OpenAI-compatible client is built lazily
    from `OPENROUTER_API_KEY` (optionally `OPENROUTER_SITE_URL` / `OPENROUTER_APP_NAME`
    for attribution), or injected for tests — so this module needs no network/key to
    import or unit-test.
    """

    def __init__(
        self,
        model_id: str = DEFAULT_OPENROUTER_MODEL,
        *,
        max_tokens: int = 1024,
        client: Any | None = None,
        api_key: str | None = None,
    ) -> None:
        self._model_id = model_id
        self._max_tokens = max_tokens
        self._client = client
        self._api_key = api_key

    def _ensure_client(self) -> Any:
        if self._client is None:
            from openai import OpenAI

            headers: dict[str, str] = {}
            site = os.getenv("OPENROUTER_SITE_URL")
            app = os.getenv("OPENROUTER_APP_NAME")
            if site:
                headers["HTTP-Referer"] = site
            if app:
                headers["X-Title"] = app
            self._client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self._api_key or os.environ["OPENROUTER_API_KEY"],
                default_headers=headers or None,
            )
        return self._client

    def complete(
        self,
        *,
        system: str,
        prompt: str,
        inputs: dict[str, str],
        response_format: dict[str, Any] | None = None,
    ) -> RecordedCall:
        client = self._ensure_client()
        kwargs: dict[str, Any] = {
            "model": self._model_id,
            "max_tokens": self._max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        }
        if response_format is not None:
            kwargs["response_format"] = response_format
        response = client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        return RecordedCall(
            model_id=self._model_id,
            system=system,
            prompt=prompt,
            inputs=dict(inputs),
            output=str(content or ""),
        )


def extract_json(text: str) -> dict[str, Any]:
    """Tolerantly extract a single JSON object from LLM output.

    Handles bare JSON, ```json fenced blocks, and JSON embedded in prose by scanning
    for the first balanced `{...}`. Raises ValueError if no JSON object is found —
    the safety net behind structured-output `response_format`, since not every model
    honors it.
    """
    s = text.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z0-9]*\n?", "", s)
        s = re.sub(r"\n?```$", "", s).strip()

    try:
        parsed = json.loads(s)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    start = s.find("{")
    if start == -1:
        raise ValueError("no JSON object found in text")
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(s)):
        ch = s[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                obj = json.loads(s[start : i + 1])
                if not isinstance(obj, dict):
                    raise ValueError("extracted JSON is not an object")
                return obj
    raise ValueError("unbalanced JSON object in text")


def build_llm_from_env() -> LLMClient:
    """Select the runtime LLM provider from env (ADR-0009).

    `OPENROUTER_API_KEY` → OpenRouter (multi-model, `OPENROUTER_MODEL`); otherwise
    Anthropic direct. Stub clients are injected explicitly in tests, never returned
    here (they need preset outputs).
    """
    if os.getenv("OPENROUTER_API_KEY"):
        return OpenRouterLLMClient(
            os.getenv("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL),
            max_tokens=int(os.getenv("OPENROUTER_MAX_TOKENS", "1024")),
        )
    return AnthropicLLMClient()


__all__ = [
    "RecordedCall",
    "LLMClient",
    "StubLLMClient",
    "OpenRouterLLMClient",
    "AnthropicLLMClient",
    "build_llm_from_env",
    "extract_json",
    "DEFAULT_OPENROUTER_MODEL",
    "JSON_OBJECT_RESPONSE_FORMAT",
]
