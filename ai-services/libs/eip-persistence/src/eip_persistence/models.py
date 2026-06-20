"""Immutable, append-only verdict record (ADR-0008)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class VerdictRecord(BaseModel):
    """One versioned verdict snapshot. Frozen — records are never mutated, only
    superseded by a higher-`version` append (INV-TEMPORAL)."""

    model_config = ConfigDict(frozen=True)

    claim_id: str
    version: int = Field(ge=1, description="Monotonic per-claim version (1-based).")
    verdict: str
    score: float
    weights_version: str
    knowledge_time: datetime = Field(description="When this assessment was recorded.")
    event_time: datetime | None = Field(
        default=None, description="When the underlying event occurred, if known."
    )
    payload: dict[str, Any] = Field(
        default_factory=dict, description="Full result snapshot (e.g. TrustResult JSON)."
    )
