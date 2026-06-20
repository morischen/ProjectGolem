"""Tests for claim-type / domain-aware weight profiles."""

import pytest

from eip_trust import (
    DEFAULT_WEIGHTS,
    HISTORICAL_WEIGHTS,
    ClaimType,
    Evidence,
    EvidenceRelation,
    score_claim,
    weights_for,
)


def _weights_sum(w) -> float:
    return (
        w.source_reliability + w.corroboration + w.evidence_quality + w.independence + w.freshness
    )


def test_default_profile_selected():
    assert weights_for() is DEFAULT_WEIGHTS
    assert weights_for(ClaimType.EMPIRICAL) is DEFAULT_WEIGHTS


def test_historical_profile_discounts_freshness_and_still_sums_to_one():
    w = weights_for(historical=True)
    assert w is HISTORICAL_WEIGHTS
    assert w.freshness < DEFAULT_WEIGHTS.freshness
    assert w.source_reliability > DEFAULT_WEIGHTS.source_reliability
    assert _weights_sum(w) == pytest.approx(1.0)


def test_profiles_have_distinct_versions():
    # Reproducibility: each profile records a distinct, traceable version.
    assert DEFAULT_WEIGHTS.version != HISTORICAL_WEIGHTS.version


def test_historical_profile_rewards_old_strong_sources():
    # Old (freshness=0) but strong, well-corroborated evidence scores higher under
    # the historical profile because recency is discounted in favor of reliability.
    old_strong = [
        Evidence(
            id=f"s{i}",
            source_id=f"s{i}",
            source_tier=1,
            relation=EvidenceRelation.SUPPORTS,
            quality=1.0,
            freshness=0.0,
        )
        for i in range(3)
    ]
    default_result = score_claim(old_strong, weights_for())
    historical_result = score_claim(old_strong, weights_for(historical=True))

    assert historical_result.score > default_result.score
    assert historical_result.weights_version == HISTORICAL_WEIGHTS.version
