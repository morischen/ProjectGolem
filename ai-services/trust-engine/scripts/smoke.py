"""Runtime smoke check for the Trust Engine.

Exercises the public API end-to-end (beyond unit tests) and exits non-zero on
failure, so it can gate a loop. Deliberately tiny and dependency-free.
"""

from eip_trust import Evidence, EvidenceRelation, score_claim


def main() -> None:
    evidence = [
        Evidence(
            id="e1",
            source_id="s1",
            source_tier=1,
            relation=EvidenceRelation.SUPPORTS,
            quality=1.0,
            freshness=1.0,
        ),
        Evidence(
            id="e2",
            source_id="s2",
            source_tier=1,
            relation=EvidenceRelation.SUPPORTS,
            quality=1.0,
            freshness=1.0,
        ),
        Evidence(
            id="e3",
            source_id="s3",
            source_tier=2,
            relation=EvidenceRelation.CONTRADICTS,
            quality=0.6,
            freshness=0.7,
        ),
    ]
    result = score_claim(evidence)

    assert 0.0 <= result.score <= 1.0, f"score out of range: {result.score}"
    assert result.relevant_count == 3, result.relevant_count
    assert result.weights_version, "missing weights_version"
    # Serialization must satisfy the contract surface.
    dumped = result.model_dump(mode="json")
    assert dumped["verdict"] == result.verdict.value

    print(
        f"SMOKE OK: verdict={result.verdict.value} score={result.score:.3f} "
        f"net={result.net_support:+.2f} conflict={result.conflict_ratio:.2f}"
    )


if __name__ == "__main__":
    main()
