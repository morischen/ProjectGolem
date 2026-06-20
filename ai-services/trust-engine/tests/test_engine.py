"""Tests for the deterministic Trust Engine.

Covers the invariants that matter most: determinism (INV-DETERMINISM), the §10
formula, verdict mapping, uncertainty as a real outcome (INV-FORCE), explicit
contradiction modeling, and single-source (citation-laundering) resistance.
"""

import pytest

from eip_trust import (
    DEFAULT_WEIGHTS,
    Evidence,
    EvidenceRelation,
    ScoringWeights,
    Verdict,
    score_claim,
)


def ev(
    eid: str,
    relation: EvidenceRelation,
    *,
    source_id: str | None = None,
    tier: int = 1,
    quality: float = 1.0,
    freshness: float = 1.0,
) -> Evidence:
    return Evidence(
        id=eid,
        source_id=source_id or eid,  # distinct source per item by default
        source_tier=tier,
        relation=relation,
        quality=quality,
        freshness=freshness,
    )


def supports(n: int, **kw) -> list[Evidence]:
    return [ev(f"s{i}", EvidenceRelation.SUPPORTS, **kw) for i in range(n)]


def contradicts(n: int, **kw) -> list[Evidence]:
    return [ev(f"c{i}", EvidenceRelation.CONTRADICTS, **kw) for i in range(n)]


# --- Configuration -----------------------------------------------------------


def test_default_weights_sum_to_one():
    w = DEFAULT_WEIGHTS
    total = (
        w.source_reliability + w.corroboration + w.evidence_quality + w.independence + w.freshness
    )
    assert total == pytest.approx(1.0)


def test_invalid_weights_rejected():
    with pytest.raises(ValueError):
        ScoringWeights(version="bad", source_reliability=0.5)  # breaks the sum-to-1 rule


# --- Determinism (INV-DETERMINISM) -------------------------------------------


def test_scoring_is_deterministic():
    evidence = supports(2, tier=1) + contradicts(1, tier=2)
    first = score_claim(evidence)
    second = score_claim(evidence)
    assert first == second
    assert first.score == second.score


# --- Verdict mapping ---------------------------------------------------------


def test_verified_strong_corroborated_support():
    result = score_claim(supports(3, tier=1, quality=1.0, freshness=1.0))
    assert result.verdict is Verdict.VERIFIED
    assert result.score == pytest.approx(0.91875)
    assert result.net_support == pytest.approx(1.0)
    assert result.conflict_ratio == pytest.approx(0.0)


def test_false_strong_corroborated_contradiction():
    result = score_claim(contradicts(3, tier=1, quality=1.0, freshness=1.0))
    assert result.verdict is Verdict.FALSE
    assert result.score == pytest.approx(0.91875)
    assert result.net_support == pytest.approx(-1.0)


def test_likely_true_moderate_support():
    result = score_claim(supports(2, tier=3, quality=0.6, freshness=0.5))
    assert result.verdict is Verdict.LIKELY_TRUE
    assert result.score == pytest.approx(0.6125)


def test_likely_false_moderate_contradiction():
    result = score_claim(contradicts(2, tier=3, quality=0.6, freshness=0.5))
    assert result.verdict is Verdict.LIKELY_FALSE
    assert result.score == pytest.approx(0.6125)


# --- Uncertainty is a valid outcome (INV-FORCE) ------------------------------


def test_no_directional_evidence_is_insufficient():
    neutral = [
        ev("n1", EvidenceRelation.NEUTRAL),
        ev("n2", EvidenceRelation.INCONCLUSIVE),
    ]
    result = score_claim(neutral)
    assert result.verdict is Verdict.INSUFFICIENT_EVIDENCE
    assert result.score == 0.0
    assert result.relevant_count == 0


def test_empty_evidence_is_insufficient():
    assert score_claim([]).verdict is Verdict.INSUFFICIENT_EVIDENCE


def test_weak_evidence_is_insufficient():
    result = score_claim(supports(1, tier=4, quality=0.1, freshness=0.0))
    assert result.verdict is Verdict.INSUFFICIENT_EVIDENCE
    assert result.score == pytest.approx(0.25)


def test_balanced_conflict_is_mixed_not_forced():
    evidence = supports(2, tier=1) + contradicts(2, tier=1)
    result = score_claim(evidence)
    assert result.verdict is Verdict.MIXED_EVIDENCE
    assert result.conflict_ratio == pytest.approx(0.5)
    assert result.net_support == pytest.approx(0.0)


# --- Contradiction is modeled explicitly, not just labeled -------------------


def test_adding_contradiction_moves_verified_to_mixed():
    before = score_claim(supports(3, tier=1))
    assert before.verdict is Verdict.VERIFIED

    after = score_claim(supports(3, tier=1) + contradicts(3, tier=1))
    assert after.verdict is Verdict.MIXED_EVIDENCE
    assert after.conflict_ratio > before.conflict_ratio
    assert after.net_support < before.net_support


# --- Independence: single-source repetition can't reach Verified -------------


def test_single_source_repetition_does_not_reach_verified():
    """Three 'supports' all laundered through one source must not be Verified."""
    same_source = [
        ev(f"s{i}", EvidenceRelation.SUPPORTS, source_id="only-one", tier=1) for i in range(3)
    ]
    result = score_claim(same_source)
    assert result.verdict is Verdict.LIKELY_TRUE  # not VERIFIED
    assert result.breakdown.independence == pytest.approx(0.0)

    distinct = score_claim(supports(3, tier=1))
    assert distinct.verdict is Verdict.VERIFIED
    assert distinct.score > result.score


# --- Reproducibility metadata ------------------------------------------------


def test_result_records_weights_version():
    result = score_claim(supports(1, tier=1))
    assert result.weights_version == DEFAULT_WEIGHTS.version
