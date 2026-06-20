"""Run the Trust Engine over a benchmark set and compute metrics (§28.10 stub).

Metrics: verdict accuracy (overall + per difficulty) and a simple calibration
error. Per-item weights honor the item's `historical` flag (profile selection).
Deterministic: same items -> same report.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from eip_trust.benchmark.models import Band, BenchmarkItem
from eip_trust.config import weights_for
from eip_trust.engine import score_claim
from eip_trust.models import ScoringWeights, TrustResult

# Representative confidence implied by each band, for calibration error.
_BAND_CONFIDENCE: dict[Band, float] = {"low": 0.40, "medium": 0.675, "high": 0.90}


def band_for(score: float) -> Band:
    """Bucket a score into a confidence band (no false precision; §28.3)."""
    if score >= 0.80:
        return "high"
    if score >= 0.55:
        return "medium"
    return "low"


def load_items(path: str | Path) -> list[BenchmarkItem]:
    """Load a JSON array of benchmark items from disk."""
    data = json.loads(Path(path).read_text())
    return [BenchmarkItem.model_validate(d) for d in data]


@dataclass(frozen=True)
class ItemOutcome:
    item: BenchmarkItem
    result: TrustResult
    verdict_match: bool
    band: Band


@dataclass(frozen=True)
class BenchmarkReport:
    total: int
    verdict_accuracy: float
    by_difficulty: dict[str, float]
    calibration_error: float
    outcomes: list[ItemOutcome]


def run_benchmark(
    items: Sequence[BenchmarkItem],
    weights: ScoringWeights | None = None,
) -> BenchmarkReport:
    """Score every item and summarize. If `weights` is None, each item uses its
    own profile (`weights_for(historical=item.historical)`)."""
    outcomes: list[ItemOutcome] = []
    for item in items:
        w = weights if weights is not None else weights_for(historical=item.historical)
        result = score_claim(item.evidence, w)
        outcomes.append(
            ItemOutcome(
                item=item,
                result=result,
                verdict_match=result.verdict == item.expected_verdict,
                band=band_for(result.score),
            )
        )

    total = len(outcomes)
    accuracy = sum(o.verdict_match for o in outcomes) / total if total else 0.0

    by_difficulty: dict[str, float] = {}
    for difficulty in sorted({o.item.difficulty for o in outcomes}):
        group = [o for o in outcomes if o.item.difficulty == difficulty]
        by_difficulty[difficulty] = sum(o.verdict_match for o in group) / len(group)

    return BenchmarkReport(
        total=total,
        verdict_accuracy=accuracy,
        by_difficulty=by_difficulty,
        calibration_error=_calibration_error(outcomes),
        outcomes=outcomes,
    )


def _calibration_error(outcomes: Sequence[ItemOutcome]) -> float:
    """Expected-calibration-error stub: |accuracy - implied confidence| per band,
    weighted by band population. 0 = perfectly calibrated."""
    total = len(outcomes)
    if total == 0:
        return 0.0
    error = 0.0
    for band, confidence in _BAND_CONFIDENCE.items():
        group = [o for o in outcomes if o.band == band]
        if not group:
            continue
        accuracy = sum(o.verdict_match for o in group) / len(group)
        error += abs(accuracy - confidence) * (len(group) / total)
    return error
