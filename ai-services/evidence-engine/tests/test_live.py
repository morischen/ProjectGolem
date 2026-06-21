"""Live integration test — real LLM classification via build_llm_from_env().

Skipped unless an LLM key is set, so CI stays hermetic. Run it with credentials:
    set -a; . ../../.env; set +a   # or export OPENROUTER_API_KEY
    uv run pytest tests/test_live.py
"""

import os

import pytest
from eip_llm import build_llm_from_env

from eip_evidence import Candidate, StubRetriever, gather

pytestmark = pytest.mark.skipif(
    not (os.getenv("OPENROUTER_API_KEY") or os.getenv("ANTHROPIC_API_KEY")),
    reason="no LLM key set (OPENROUTER_API_KEY / ANTHROPIC_API_KEY) — live test skipped",
)

VALID_RELATIONS = {"supports", "contradicts", "neutral", "inconclusive"}


def test_live_gather_classifies():
    candidates = [
        Candidate(
            id="c1",
            source_id="s1",
            source_tier=1,
            content="Multiple outlets report City Y was struck by an air strike on 2024-01-02.",
            quality=0.8,
            freshness=0.9,
        )
    ]
    result = gather(
        "Country X struck City Y on 2024-01-02.",
        retriever=StubRetriever(candidates),
        llm=build_llm_from_env(),
    )
    assert len(result.evidence) == 1
    assert result.evidence[0].relation.value in VALID_RELATIONS
    assert result.calls[0].model_id
