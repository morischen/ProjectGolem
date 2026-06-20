"""Benchmark item model (gold-benchmark spec §28, stub).

A benchmark item pairs a claim + its classified evidence with the expected
verdict and strata tags, so the Trust Engine can be measured (verdict accuracy,
calibration) against a labeled set. This is eval tooling, not a runtime contract;
it may graduate into `contracts/` once the benchmark format stabilizes.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from eip_trust.models import Evidence, Verdict

Difficulty = Literal["trivial", "tractable", "hard", "undecidable"]
Band = Literal["low", "medium", "high"]


class BenchmarkItem(BaseModel):
    """One labeled claim + evidence, with expected outcome and §28 strata tags."""

    model_config = ConfigDict(extra="forbid")

    id: str
    claim_text: str
    expected_verdict: Verdict
    difficulty: Difficulty = "tractable"
    expected_band: Band | None = None
    historical: bool = False
    framing_pair_id: str | None = Field(
        default=None, description="Links matched opposing-framing pairs (§28.5)."
    )
    notes: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)
