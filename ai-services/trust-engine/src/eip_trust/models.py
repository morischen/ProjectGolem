"""Public domain-model facade for the Trust Engine.

Cross-service *contract* shapes are code-generated from `contracts/*.schema.json`
into `eip_trust._generated` (do not edit those — see ADR-0004). Engine-internal
config (`ScoringWeights`) is hand-authored in `eip_trust.weights`. This module
re-exports both so callers have one stable import surface (`eip_trust.models`).
"""

from eip_trust._generated import (
    Claim,
    ClaimType,
    ConfidenceBreakdown,
    Evidence,
    EvidenceRelation,
    TrustResult,
    Verdict,
)
from eip_trust.weights import ScoringWeights

__all__ = [
    "Claim",
    "ClaimType",
    "ConfidenceBreakdown",
    "Evidence",
    "EvidenceRelation",
    "ScoringWeights",
    "TrustResult",
    "Verdict",
]
