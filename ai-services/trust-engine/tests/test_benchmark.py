"""Tests for the gold-benchmark harness stub.

The seed set also serves as golden fixtures: the engine must reproduce every
labeled verdict (verdict_accuracy == 1.0).
"""

from pathlib import Path

import pytest

from eip_trust.benchmark import band_for, load_items, run_benchmark

SEED = Path(__file__).resolve().parents[1] / "benchmark" / "seed" / "cases.json"


@pytest.fixture(scope="module")
def items():
    return load_items(SEED)


def test_seed_loads(items):
    assert len(items) == 21
    assert all(it.id and it.claim_text for it in items)


def test_seed_is_golden(items):
    """Engine reproduces every labeled verdict."""
    report = run_benchmark(items)
    mismatches = [
        (o.item.id, o.result.verdict.value) for o in report.outcomes if not o.verdict_match
    ]
    assert report.verdict_accuracy == 1.0, f"mismatches: {mismatches}"


def test_report_shape(items):
    report = run_benchmark(items)
    assert report.total == len(items)
    assert set(report.by_difficulty) <= {"trivial", "tractable", "hard", "undecidable"}
    assert all(0.0 <= acc <= 1.0 for acc in report.by_difficulty.values())
    assert 0.0 <= report.calibration_error <= 1.0


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0.0, "low"),
        (0.54, "low"),
        (0.55, "medium"),
        (0.79, "medium"),
        (0.80, "high"),
        (1.0, "high"),
    ],
)
def test_band_for(score, expected):
    assert band_for(score) == expected


def test_matched_framing_pair_has_no_bias_delta(items):
    """Both framings of the same fact (identical evidence) must score identically."""
    report = run_benchmark(items)
    pair = {o.item.id: o.result.score for o in report.outcomes if o.item.framing_pair_id == "fp1"}
    assert len(pair) == 2
    scores = list(pair.values())
    assert scores[0] == pytest.approx(scores[1])


def test_historical_item_uses_historical_profile(items):
    report = run_benchmark(items)
    hist = next(o for o in report.outcomes if o.item.id == "historical-old-strong")
    assert hist.result.weights_version.endswith("historical")
    assert hist.verdict_match
