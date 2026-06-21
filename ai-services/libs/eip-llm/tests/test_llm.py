"""Hermetic tests for the recorded LLM wrappers and env-based provider selection."""

from types import SimpleNamespace

import pytest

from eip_llm import (
    JSON_OBJECT_RESPONSE_FORMAT,
    AnthropicLLMClient,
    LLMError,
    OpenRouterLLMClient,
    RecordedCall,
    StubLLMClient,
    build_llm_from_env,
    extract_json,
)


def test_stub_records_and_sequences_outputs():
    stub = StubLLMClient(["a", "b"], model_id="stub-x")
    first = stub.complete(system="s", prompt="p1", inputs={"k": "1"})
    second = stub.complete(system="s", prompt="p2", inputs={"k": "2"})
    third = stub.complete(system="s", prompt="p3", inputs={"k": "3"})  # last repeats

    assert isinstance(first, RecordedCall)
    assert [c.output for c in (first, second, third)] == ["a", "b", "b"]
    assert first.model_id == "stub-x"
    assert len(stub.calls) == 3


class _FakeOpenAI:
    """Minimal OpenAI-compatible stand-in: records the call, returns canned text."""

    def __init__(self, content: str | None, finish_reason: str = "stop") -> None:
        self.last_kwargs: dict | None = None
        completions = SimpleNamespace(create=self._create)
        self.chat = SimpleNamespace(completions=completions)
        self._content = content
        self._finish_reason = finish_reason

    def _create(self, **kwargs):
        self.last_kwargs = kwargs
        message = SimpleNamespace(content=self._content)
        choice = SimpleNamespace(message=message, finish_reason=self._finish_reason)
        return SimpleNamespace(choices=[choice])


def test_openrouter_maps_to_chat_completions_and_records():
    fake = _FakeOpenAI('{"relation": "supports"}')
    client = OpenRouterLLMClient("anthropic/claude-opus-4.8", client=fake)
    call = client.complete(system="SYS", prompt="PROMPT", inputs={"id": "c1"})

    assert call.output == '{"relation": "supports"}'
    assert call.model_id == "anthropic/claude-opus-4.8"
    assert call.inputs == {"id": "c1"}
    # system + user messages forwarded in OpenAI-compatible shape
    assert fake.last_kwargs is not None
    assert fake.last_kwargs["model"] == "anthropic/claude-opus-4.8"
    roles = [m["role"] for m in fake.last_kwargs["messages"]]
    assert roles == ["system", "user"]


def test_openrouter_raises_on_empty_or_refused_completion():
    client = OpenRouterLLMClient("x/y", client=_FakeOpenAI(None, finish_reason="content_filter"))
    with pytest.raises(LLMError):
        client.complete(system="s", prompt="p", inputs={})


def test_openrouter_accepts_timeout_and_retry_config():
    fake = _FakeOpenAI('{"ok": true}')
    client = OpenRouterLLMClient("x/y", timeout=5.0, max_retries=0, client=fake)
    assert client.complete(system="s", prompt="p", inputs={}).output == '{"ok": true}'


def test_build_llm_from_env_prefers_openrouter(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "openai/gpt-5")
    client = build_llm_from_env()
    assert isinstance(client, OpenRouterLLMClient)


def test_build_llm_from_env_falls_back_to_anthropic(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert isinstance(build_llm_from_env(), AnthropicLLMClient)


def test_openrouter_forwards_response_format():
    fake = _FakeOpenAI('{"ok": true}')
    client = OpenRouterLLMClient("x/y", client=fake)
    client.complete(system="s", prompt="p", inputs={}, response_format=JSON_OBJECT_RESPONSE_FORMAT)
    assert fake.last_kwargs is not None
    assert fake.last_kwargs["response_format"] == {"type": "json_object"}
    assert fake.last_kwargs["max_tokens"] == 1024


class TestExtractJson:
    def test_plain_object(self):
        assert extract_json('{"a": 1}') == {"a": 1}

    def test_fenced_block(self):
        assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}

    def test_embedded_in_prose(self):
        text = 'Sure! Here it is:\n{"relation": "supports"}\nHope that helps.'
        assert extract_json(text) == {"relation": "supports"}

    def test_ignores_braces_inside_strings(self):
        assert extract_json('{"note": "a } brace in a string"}') == {
            "note": "a } brace in a string"
        }

    def test_raises_without_object(self):
        with pytest.raises(ValueError):
            extract_json("no json here")
