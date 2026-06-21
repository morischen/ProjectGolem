"""Calibration harness tests — hermetic (stub) + guarded live."""

import json
import os

import pytest
from eip_evidence import Candidate
from eip_llm import StubLLMClient, build_llm_from_env

from calibration import CalibrationItem, run_calibration


def _item(expected_relation: str, expected_verdict: str) -> CalibrationItem:
    return CalibrationItem(
        claim_text="Country X struck City Y.",
        candidate=Candidate(
            id="c1", source_id="s1", source_tier=1, content="report", quality=1.0, freshness=1.0
        ),
        expected_relation=expected_relation,
        expected_verdict=expected_verdict,
    )


def test_run_calibration_all_correct():
    # One tier-1 supporting source -> Likely True (single-source: low independence).
    items = [_item("supports", "Likely True"), _item("supports", "Likely True")]
    llm = StubLLMClient([json.dumps({"relation": "supports"})] * 2)
    report = run_calibration(items, llm=llm)
    assert report.total == 2
    assert report.relation_accuracy == 1.0
    assert report.verdict_accuracy == 1.0


def test_run_calibration_counts_relation_mismatch():
    # Label says "contradicts" but the (stub) model says "supports".
    items = [_item("contradicts", "Likely False")]
    report = run_calibration(items, llm=StubLLMClient(json.dumps({"relation": "supports"})))
    assert report.relation_accuracy == 0.0


@pytest.mark.skipif(
    not (os.getenv("OPENROUTER_API_KEY") or os.getenv("ANTHROPIC_API_KEY")),
    reason="no LLM key set — live calibration skipped",
)
def test_live_calibration_runs_and_reports():
    item = CalibrationItem(
        claim_text="Country X launched an air strike on City Y on 2024-01-02.",
        candidate=Candidate(
            id="c1",
            source_id="s1",
            source_tier=1,
            content="Multiple outlets confirm City Y was hit by an air strike on 2024-01-02.",
            quality=0.8,
            freshness=0.9,
        ),
        expected_relation="supports",
        expected_verdict="Likely True",
    )
    report = run_calibration([item], llm=build_llm_from_env())
    assert report.total == 1
    assert 0.0 <= report.relation_accuracy <= 1.0
    assert 0.0 <= report.verdict_accuracy <= 1.0
