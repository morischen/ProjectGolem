"""Engine-internal scoring configuration (hand-authored).

`ScoringWeights` carries behaviour (the sum-to-1 validator) and is internal to the
Trust Engine, not a cross-service contract — so it lives here, not in `contracts/`
(ADR-0004). Contract *shapes* are generated under `_generated/`.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


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
    strength_floor: float = Field(
        0.30, ge=0.0, le=1.0, description="Below this strength -> Insufficient."
    )
    mixed_conflict_threshold: float = Field(
        0.35, ge=0.0, le=0.5, description="Min minority-mass share -> Mixed Evidence."
    )
    verified_threshold: float = Field(
        0.80, ge=0.0, le=1.0, description="At/above -> Verified or False."
    )

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
