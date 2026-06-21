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


class ConfigRecord(BaseModel):
    """One versioned configuration snapshot (e.g. a scoring-weights profile).

    Append-only and frozen: methodology changes create a new version, never mutate a
    prior one, so historical verdicts stay reproducible against the config that
    produced them (INV-REPRO / INV-TEMPORAL). The store is schema-agnostic — the
    payload's shape (e.g. ScoringWeights) is owned by the consuming service."""

    model_config = ConfigDict(frozen=True)

    profile: str = Field(description="Config namespace, e.g. 'default' or 'historical'.")
    version: int = Field(ge=1, description="Monotonic per-profile version (1-based).")
    payload: dict[str, Any] = Field(description="The configuration document (e.g. weights).")
    knowledge_time: datetime = Field(description="When this config version was recorded.")
    actor: str | None = Field(default=None, description="Who created this version, if known.")
    note: str | None = Field(default=None, description="Optional change rationale.")


class AuditRecord(BaseModel):
    """One append-only audit-log entry for an admin mutation. Frozen and never
    deleted — the tamper-evident record of who changed what, when."""

    model_config = ConfigDict(frozen=True)

    id: int = Field(ge=1, description="Monotonic global sequence (1-based).")
    actor: str = Field(description="Who performed the action.")
    action: str = Field(description="What was done, e.g. 'config.update'.")
    target: str = Field(description="What was acted on, e.g. 'config:default'.")
    knowledge_time: datetime = Field(description="When the action was recorded.")
    before: dict[str, Any] | None = Field(default=None, description="Prior state, if any.")
    after: dict[str, Any] | None = Field(default=None, description="New state, if any.")
