"""The optional independence override (ADR-0007) replaces the count-based heuristic."""

import pytest

from eip_trust import Evidence, EvidenceRelation, Verdict, score_claim


def supports(
    n: int, *, tier: int = 1, quality: float = 1.0, freshness: float = 1.0
) -> list[Evidence]:
    return [
        Evidence(
            id=f"s{i}",
            source_id=f"s{i}",
            source_tier=tier,
            relation=EvidenceRelation.SUPPORTS,
            quality=quality,
            freshness=freshness,
        )
        for i in range(n)
    ]


def test_override_replaces_computed_independence():
    evidence = supports(3, tier=1)  # count-based independence = 1 - 1/3 = 0.667
    default = score_claim(evidence)
    overridden = score_claim(evidence, independence=0.0)

    assert default.breakdown.independence == pytest.approx(2 / 3)
    assert overridden.breakdown.independence == 0.0
    assert overridden.score < default.score  # laundered corroboration scores lower


def test_override_is_clamped():
    result = score_claim(supports(2), independence=5.0)
    assert result.breakdown.independence == 1.0


def test_laundering_can_flip_verified_to_likely_true():
    # 3 distinct tier-2 sources -> count independence 0.667 -> Verified.
    evidence = supports(3, tier=2, quality=0.9, freshness=0.8)
    assert score_claim(evidence).verdict is Verdict.VERIFIED

    # The graph reveals they share one origin -> independence_ratio = 1/3 -> downgraded.
    laundered = score_claim(evidence, independence=1 / 3)
    assert laundered.verdict is Verdict.LIKELY_TRUE
    assert laundered.score < 0.80
