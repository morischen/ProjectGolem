"""Deterministic Trust Engine for the Evidence Intelligence Platform.

The Trust Engine is the *only* component that produces confidence scores and
verdicts, and it does so deterministically from a versioned formula. LLMs never
score (see ADR-0003 / INV-DETERMINISM).
"""

from eip_trust.config import DEFAULT_WEIGHTS, HISTORICAL_WEIGHTS, weights_for
from eip_trust.engine import score_claim
from eip_trust.freshness import freshness_from_age_days
from eip_trust.models import (
    Claim,
    ClaimType,
    ConfidenceBreakdown,
    Evidence,
    EvidenceRelation,
    ScoringWeights,
    TrustResult,
    Verdict,
)

__all__ = [
    "DEFAULT_WEIGHTS",
    "HISTORICAL_WEIGHTS",
    "weights_for",
    "score_claim",
    "freshness_from_age_days",
    "Claim",
    "ClaimType",
    "ConfidenceBreakdown",
    "Evidence",
    "EvidenceRelation",
    "ScoringWeights",
    "TrustResult",
    "Verdict",
]
