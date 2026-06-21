"""Operational metrics for the admin dashboard (A4).

Computes a live snapshot from the gold benchmark + the runtime stores: verdict
accuracy and calibration error (§28 / §26 gate metrics), human-review queue health,
and the verdict corpus size. Pure read — no scoring happens here (INV-DETERMINISM);
the benchmark re-runs the deterministic engine over the labeled seed set.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from eip_persistence import ReviewStore, VerdictStore

from eip_trust.benchmark import load_items, run_benchmark

# trust-engine/benchmark/seed/cases.json (this file is src/eip_trust/metrics.py).
DEFAULT_SEED_PATH = Path(__file__).resolve().parents[2] / "benchmark" / "seed" / "cases.json"


def benchmark_metrics(seed_path: Path | None = None) -> dict[str, Any] | None:
    """Run the gold benchmark and summarize. Returns None if the seed is unavailable."""
    path = seed_path or DEFAULT_SEED_PATH
    if not path.exists():
        return None
    report = run_benchmark(load_items(path))
    return {
        "total": report.total,
        "verdict_accuracy": report.verdict_accuracy,
        "calibration_error": report.calibration_error,
        "by_difficulty": report.by_difficulty,
    }


def queue_health(review_store: ReviewStore) -> dict[str, Any]:
    """Open/resolved counts and a per-kind breakdown of the review queue."""
    items = review_store.list(limit=10_000)
    by_kind: dict[str, int] = {}
    open_count = 0
    resolved_count = 0
    for item in items:
        by_kind[item.kind] = by_kind.get(item.kind, 0) + 1
        if item.status == "open":
            open_count += 1
        elif item.status == "resolved":
            resolved_count += 1
    return {"open": open_count, "resolved": resolved_count, "by_kind": by_kind}


def claims_count(verdict_store: VerdictStore | None) -> int:
    """Number of distinct claims with at least one verdict."""
    if verdict_store is None:
        return 0
    return len(verdict_store.list_claims(limit=100_000))


def compute_metrics(
    *,
    verdict_store: VerdictStore | None,
    review_store: ReviewStore,
    seed_path: Path | None = None,
) -> dict[str, Any]:
    return {
        "benchmark": benchmark_metrics(seed_path),
        "queue": queue_health(review_store),
        "claims_count": claims_count(verdict_store),
    }
