"""Pure helper to derive a normalized freshness signal from evidence age.

Freshness is a precomputed [0, 1] input to the Trust Engine; callers may compute
it however they like. This is one deterministic option: exponential decay by age.
No clock is read here — the caller supplies the age in days — so the scoring path
stays pure and reproducible (INV-DETERMINISM / INV-REPRO).
"""

from __future__ import annotations


def freshness_from_age_days(age_days: float, half_life_days: float = 365.0) -> float:
    """Map evidence age to freshness in (0, 1].

    1.0 at age 0; halves every `half_life_days`. Use a large half-life for domains
    where recency matters little (e.g. settled history).
    """
    if age_days < 0:
        raise ValueError(f"age_days must be >= 0, got {age_days}")
    if half_life_days <= 0:
        raise ValueError(f"half_life_days must be > 0, got {half_life_days}")
    return float(0.5 ** (age_days / half_life_days))
