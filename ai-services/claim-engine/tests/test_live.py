"""Live integration test — real LLM via build_llm_from_env().

Skipped unless an LLM key is set, so CI stays hermetic. Run it with credentials:
    set -a; . ../../.env; set +a   # or export OPENROUTER_API_KEY
    uv run pytest tests/test_live.py
"""

import os

import pytest
from eip_llm import build_llm_from_env

from eip_claim import extract_claim

pytestmark = pytest.mark.skipif(
    not (os.getenv("OPENROUTER_API_KEY") or os.getenv("ANTHROPIC_API_KEY")),
    reason="no LLM key set (OPENROUTER_API_KEY / ANTHROPIC_API_KEY) — live test skipped",
)

VALID_CLAIM_TYPES = {"empirical", "legal", "definitional", "predictive", "normative"}


def test_live_extract_claim():
    result = extract_claim(
        "Country X launched an air strike on City Y on 2024-01-02.",
        claim_id="live-1",
        llm=build_llm_from_env(),
    )
    assert result.claim.id == "live-1"
    assert result.claim.claim_type.value in VALID_CLAIM_TYPES
    assert result.call.model_id  # recorded for reproducibility
