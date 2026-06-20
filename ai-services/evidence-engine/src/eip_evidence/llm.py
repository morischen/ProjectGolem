"""LLM access via a recorded wrapper (ADR-0005).

Mirrors the claim-engine wrapper. TODO: extract a shared `eip_llm` lib so this
isn't duplicated per service. The LLM classifies the relation only — it never
produces a score or verdict (INV-DETERMINISM).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class RecordedCall:
    model_id: str
    system: str
    prompt: str
    inputs: dict[str, str]
    output: str


@runtime_checkable
class LLMClient(Protocol):
    def complete(self, *, system: str, prompt: str, inputs: dict[str, str]) -> RecordedCall: ...


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

    def complete(self, *, system: str, prompt: str, inputs: dict[str, str]) -> RecordedCall:
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

    def __init__(self, model_id: str = "claude-opus-4-8", max_tokens: int = 1000) -> None:
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
