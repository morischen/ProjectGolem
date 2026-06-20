"""Deterministic Trust Engine for the Evidence Intelligence Platform.

The Trust Engine is the *only* component that produces confidence scores and
verdicts, and it does so deterministically from a versioned formula. LLMs never
score (see ADR-0003 / INV-DETERMINISM).
"""

from eip_trust.config import DEFAULT_WEIGHTS
from eip_trust.engine import score_claim
from eip_trust.models import (
    ConfidenceBreakdown,
    Evidence,
    EvidenceRelation,
    ScoringWeights,
    TrustResult,
    Verdict,
)

__all__ = [
    "DEFAULT_WEIGHTS",
    "score_claim",
    "ConfidenceBreakdown",
    "Evidence",
    "EvidenceRelation",
    "ScoringWeights",
    "TrustResult",
    "Verdict",
]
