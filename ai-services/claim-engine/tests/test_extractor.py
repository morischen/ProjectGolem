"""Tests for claim extraction using the deterministic stub LLM client."""

import json

import pytest
from pydantic import ValidationError

from eip_claim import Claim, ClaimType, StubLLMClient, build_prompt, extract_claim

VALID_OUTPUT = json.dumps(
    {
        "text": "Country X launched an attack on City Y on 2024-01-02.",
        "claim_type": "empirical",
        "actors": ["Country X"],
        "targets": ["City Y"],
        "events": ["attack"],
        "locations": ["City Y"],
        "dates": ["2024-01-02"],
        "assertions": ["Country X attacked City Y"],
    }
)


def test_extracts_normalized_claim():
    llm = StubLLMClient(VALID_OUTPUT)
    result = extract_claim("Country X attacked City Y yesterday.", claim_id="c1", llm=llm)
    assert isinstance(result.claim, Claim)
    assert result.claim.id == "c1"
    assert result.claim.claim_type is ClaimType.EMPIRICAL
    assert result.claim.actors == ["Country X"]


def test_records_call_for_reproducibility():
    llm = StubLLMClient(VALID_OUTPUT, model_id="stub-1")
    result = extract_claim("text here", claim_id="c2", llm=llm)
    assert result.call.model_id == "stub-1"
    assert result.call.inputs == {"claim_id": "c2", "text": "text here"}
    assert "text here" in result.call.prompt
    assert result.call.output == VALID_OUTPUT
    assert len(llm.calls) == 1


def test_injects_claim_id_when_missing():
    result = extract_claim("t", claim_id="c3", llm=StubLLMClient(VALID_OUTPUT))
    assert result.claim.id == "c3"


def test_explicit_id_in_output_is_preserved():
    out = json.dumps({"id": "from-llm", "text": "t", "claim_type": "legal"})
    result = extract_claim("t", claim_id="c4", llm=StubLLMClient(out))
    assert result.claim.id == "from-llm"  # setdefault must not override


def test_invalid_json_raises():
    with pytest.raises(json.JSONDecodeError):
        extract_claim("t", claim_id="c5", llm=StubLLMClient("not json"))


def test_invalid_claim_type_raises():
    out = json.dumps({"text": "t", "claim_type": "bogus"})
    with pytest.raises(ValidationError):
        extract_claim("t", claim_id="c6", llm=StubLLMClient(out))


def test_build_prompt_includes_text_and_id():
    prompt = build_prompt("hello world", "c7")
    assert "hello world" in prompt
    assert "c7" in prompt
