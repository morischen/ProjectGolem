"""Deterministic scoring.

`score_claim` is a pure function: same inputs + same weights version always yield
the same `TrustResult`. No LLM calls, no network, no I/O, no wall-clock — this is
the architectural guarantee behind INV-DETERMINISM / ADR-0003.

Confidence = blueprint §10 weighted sum of five components, each in [0, 1]:

    0.30 * source_reliability
  + 0.25 * corroboration
  + 0.20 * evidence_quality
  + 0.15 * independence
  + 0.10 * freshness

Contradiction is modeled explicitly as an opposing mass, not merely a label: a
claim with substantial evidence on both sides resolves to Mixed Evidence rather
than being forced to a side (INV-FORCE).
"""

from __future__ import annotations

from collections.abc import Sequence

from eip_trust.config import DEFAULT_WEIGHTS
from eip_trust.models import (
    ConfidenceBreakdown,
    Evidence,
    EvidenceRelation,
    ScoringWeights,
    TrustResult,
    Verdict,
)

_DIRECTIONAL = (EvidenceRelation.SUPPORTS, EvidenceRelation.CONTRADICTS)


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _insufficient(
    weights: ScoringWeights, relevant: int, supporting: int, contradicting: int
) -> TrustResult:
    return TrustResult(
        score=0.0,
        verdict=Verdict.INSUFFICIENT_EVIDENCE,
        breakdown=ConfidenceBreakdown(
            source_reliability=0.0,
            corroboration=0.0,
            evidence_quality=0.0,
            independence=0.0,
            freshness=0.0,
            weighted_total=0.0,
        ),
        weights_version=weights.version,
        relevant_count=relevant,
        supporting_count=supporting,
        contradicting_count=contradicting,
        net_support=0.0,
        conflict_ratio=0.0,
    )


def score_claim(
    evidence: Sequence[Evidence],
    weights: ScoringWeights = DEFAULT_WEIGHTS,
    *,
    independence: float | None = None,
) -> TrustResult:
    """Score a claim from its classified evidence. Pure and deterministic.

    `independence` optionally overrides the count-based independence heuristic with a
    precomputed [0,1] signal — e.g. the Evidence Engine's graph-derived
    `independence_ratio`, which detects shared-origin / citation-laundering so
    apparent corroboration isn't over-credited (ADR-0007).
    """

    relevant = [e for e in evidence if e.relation in _DIRECTIONAL]
    supports = [e for e in relevant if e.relation is EvidenceRelation.SUPPORTS]
    contradicts = [e for e in relevant if e.relation is EvidenceRelation.CONTRADICTS]

    # No directional evidence at all -> we cannot conclude (INV-FORCE).
    if not relevant:
        return _insufficient(weights, 0, len(supports), len(contradicts))

    def mass(e: Evidence) -> float:
        return weights.tier_reliability[e.source_tier] * e.quality

    support_mass = sum(mass(e) for e in supports)
    contradict_mass = sum(mass(e) for e in contradicts)
    total_mass = support_mass + contradict_mass

    # All evidence carries zero mass (e.g. quality 0) -> direction undeterminable.
    if total_mass <= 0.0:
        return _insufficient(weights, len(relevant), len(supports), len(contradicts))

    net_support = (support_mass - contradict_mass) / total_mass
    conflict_ratio = min(support_mass, contradict_mass) / total_mass

    # --- Five components, each normalized to [0, 1] ---
    source_reliability = _mean([weights.tier_reliability[e.source_tier] for e in relevant])
    evidence_quality = _mean([e.quality for e in relevant])
    freshness = _mean([e.freshness for e in relevant])

    distinct_total = len({e.source_id for e in relevant})
    computed_independence = 1.0 - 1.0 / distinct_total if distinct_total > 0 else 0.0
    independence_value = (
        computed_independence if independence is None else max(0.0, min(1.0, independence))
    )

    dominant = supports if support_mass >= contradict_mass else contradicts
    distinct_dominant = len({e.source_id for e in dominant})
    corroboration = 1.0 - 0.5**distinct_dominant if distinct_dominant > 0 else 0.0

    weighted_total = (
        weights.source_reliability * source_reliability
        + weights.corroboration * corroboration
        + weights.evidence_quality * evidence_quality
        + weights.independence * independence_value
        + weights.freshness * freshness
    )

    breakdown = ConfidenceBreakdown(
        source_reliability=source_reliability,
        corroboration=corroboration,
        evidence_quality=evidence_quality,
        independence=independence_value,
        freshness=freshness,
        weighted_total=weighted_total,
    )

    verdict = _verdict_for(weighted_total, net_support, conflict_ratio, weights)

    return TrustResult(
        score=weighted_total,
        verdict=verdict,
        breakdown=breakdown,
        weights_version=weights.version,
        relevant_count=len(relevant),
        supporting_count=len(supports),
        contradicting_count=len(contradicts),
        net_support=net_support,
        conflict_ratio=conflict_ratio,
    )


def _verdict_for(
    score: float,
    net_support: float,
    conflict_ratio: float,
    weights: ScoringWeights,
) -> Verdict:
    """Map (strength, direction, conflict) to a verdict. Order matters.

    1. Too weak overall  -> Insufficient.
    2. Substantial both sides -> Mixed (never force a side, INV-FORCE).
    3. Otherwise directional: magnitude decides Verified/False vs Likely.
    """
    if score < weights.strength_floor:
        return Verdict.INSUFFICIENT_EVIDENCE
    if conflict_ratio >= weights.mixed_conflict_threshold:
        return Verdict.MIXED_EVIDENCE
    if net_support > 0:
        return Verdict.VERIFIED if score >= weights.verified_threshold else Verdict.LIKELY_TRUE
    return Verdict.FALSE if score >= weights.verified_threshold else Verdict.LIKELY_FALSE
