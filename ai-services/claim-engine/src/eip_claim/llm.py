"""LLM access via a recorded wrapper.

Every LLM call returns a `RecordedCall` capturing the model id, prompt, and inputs
alongside the output — so any LLM-assisted result is reproducible (INV-REPRO,
ADR-0005). The LLM does language work only (extraction, classification); it never
produces a confidence score or verdict (INV-DETERMINISM, ADR-0003).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class RecordedCall:
    """An LLM call and everything needed to reproduce it."""

    model_id: str
    system: str
    prompt: str
    inputs: dict[str, str]
    output: str


@runtime_checkable
class LLMClient(Protocol):
    """Minimal text-completion surface. Implementations must record the call."""

    def complete(self, *, system: str, prompt: str, inputs: dict[str, str]) -> RecordedCall: ...


class StubLLMClient:
    """Deterministic client for tests/offline use: returns a preset output and
    records every call. No network."""

    def __init__(self, output: str, model_id: str = "stub") -> None:
        self._output = output
        self._model_id = model_id
        self.calls: list[RecordedCall] = []

    def complete(self, *, system: str, prompt: str, inputs: dict[str, str]) -> RecordedCall:
        call = RecordedCall(
            model_id=self._model_id,
            system=system,
            prompt=prompt,
            inputs=dict(inputs),
            output=self._output,
        )
        self.calls.append(call)
        return call


class AnthropicLLMClient:
    """Real client backed by the Anthropic SDK (scaffold — not exercised in CI).

    Defaults to Claude Opus 4.8 with adaptive thinking. Records the call for
    reproducibility. Requires `ANTHROPIC_API_KEY` and network access at runtime.
    """

    def __init__(self, model_id: str = "claude-opus-4-8", max_tokens: int = 2000) -> None:
        self._model_id = model_id
        self._max_tokens = max_tokens

    def complete(self, *, system: str, prompt: str, inputs: dict[str, str]) -> RecordedCall:
        import anthropic

        client = anthropic.Anthropic()
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
