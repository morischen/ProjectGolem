"""Domain models for the Trust Engine.

These are hand-authored Pydantic models for the first vertical. Per ARCHITECTURE.md
§3, cross-service shapes will eventually be generated from `contracts/`; that codegen
toolchain is an open ADR decision, so for now the shared shapes live here. Keep this
module free of any I/O or LLM dependency — it is part of the deterministic core.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, model_validator


class EvidenceRelation(str, Enum):
    """How a piece of evidence relates to the claim under assessment."""

    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    NEUTRAL = "neutral"
    INCONCLUSIVE = "inconclusive"


class Verdict(str, Enum):
    """The allowed verdict outcomes (base blueprint §9).

    Insufficient and Mixed are first-class, valid results — the engine must never
    force a definite conclusion (INV-FORCE).
    """

    VERIFIED = "Verified"
    LIKELY_TRUE = "Likely True"
    MIXED_EVIDENCE = "Mixed Evidence"
    INSUFFICIENT_EVIDENCE = "Insufficient Evidence"
    LIKELY_FALSE = "Likely False"
    FALSE = "False"


class Evidence(BaseModel):
    """A single, classified piece of evidence bearing on a claim.

    `quality` and `freshness` are normalized [0, 1] signals computed upstream
    (evidence classification / retrieval). The Trust Engine consumes them as given
    so its scoring path stays pure and deterministic.
    """

    id: str
    source_id: str = Field(description="Stable id of the originating source, for independence/corroboration.")
    source_tier: int = Field(ge=1, le=4, description="1=primary, 2=trusted reporting, 3=context, 4=emerging.")
    relation: EvidenceRelation
    quality: float = Field(ge=0.0, le=1.0, description="Strength of the supporting material.")
    freshness: float = Field(ge=0.0, le=1.0, description="Recency, normalized; precomputed upstream.")


class ScoringWeights(BaseModel):
    """Versioned scoring configuration (base blueprint §10).

    The five component weights must sum to 1.0. `version` is recorded on every
    result so verdicts remain reproducible against the config that produced them
    (INV-REPRO / INV-TEMPORAL).
    """

    version: str

    # Component weights (must sum to 1.0).
    source_reliability: float = 0.30
    corroboration: float = 0.25
    evidence_quality: float = 0.20
    independence: float = 0.15
    freshness: float = 0.10

    # Per-tier baseline reliability.
    tier_reliability: dict[int, float] = Field(
        default_factory=lambda: {1: 1.0, 2: 0.8, 3: 0.6, 4: 0.35}
    )

    # Verdict-mapping thresholds.
    strength_floor: float = Field(0.30, ge=0.0, le=1.0, description="Below this strength -> Insufficient.")
    mixed_conflict_threshold: float = Field(
        0.35, ge=0.0, le=0.5, description="Min minority-mass share -> Mixed Evidence."
    )
    verified_threshold: float = Field(0.80, ge=0.0, le=1.0, description="At/above -> Verified or False.")

    @model_validator(mode="after")
    def _weights_sum_to_one(self) -> ScoringWeights:
        total = (
            self.source_reliability
            + self.corroboration
            + self.evidence_quality
            + self.independence
            + self.freshness
        )
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"Component weights must sum to 1.0, got {total}")
        return self


class ConfidenceBreakdown(BaseModel):
    """Per-component values (each [0, 1]) and the weighted total — full explainability."""

    source_reliability: float
    corroboration: float
    evidence_quality: float
    independence: float
    freshness: float
    weighted_total: float


class TrustResult(BaseModel):
    """The deterministic output: a verdict snapshot with its full scoring breakdown."""

    score: float
    verdict: Verdict
    breakdown: ConfidenceBreakdown
    weights_version: str
    relevant_count: int
    supporting_count: int
    contradicting_count: int
    net_support: float = Field(description="(support_mass - contradict_mass) / total_mass, in [-1, 1].")
    conflict_ratio: float = Field(description="minority_mass / total_mass, in [0, 0.5].")
