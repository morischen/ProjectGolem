"""Run the seed benchmark and print a report. Exits non-zero if the engine fails
to reproduce the labeled verdicts (the seed doubles as golden fixtures), so this
can gate a loop.
"""

import sys
from pathlib import Path

from eip_trust.benchmark import load_items, run_benchmark

SEED = Path(__file__).resolve().parent.parent / "benchmark" / "seed" / "cases.json"


def main() -> int:
    items = load_items(SEED)
    report = run_benchmark(items)

    print(f"Benchmark: {SEED.name}  ({report.total} items)")
    print("-" * 72)
    print(f"{'id':<24}{'expected':<22}{'predicted':<22}{'score':>5}")
    for o in report.outcomes:
        flag = "" if o.verdict_match else "  <-- MISMATCH"
        print(
            f"{o.item.id:<24}{o.item.expected_verdict.value:<22}"
            f"{o.result.verdict.value:<22}{o.result.score:>5.2f}{flag}"
        )
    print("-" * 72)
    print(f"verdict accuracy : {report.verdict_accuracy:.1%}")
    print(f"by difficulty    : {report.by_difficulty}")
    print(f"calibration error: {report.calibration_error:.3f}")

    if report.verdict_accuracy < 1.0:
        print("\nFAIL: engine did not reproduce all labeled verdicts.", file=sys.stderr)
        return 1
    print("\nBENCH OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
