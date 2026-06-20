"""Versioned scoring configuration and profile selection.

Weight/threshold changes are governance events: bump the version string so that
historical verdicts remain reproducible against the config that produced them
(INV-REPRO). Profiles let scoring be domain/claim-type aware (blueprint §10/§23):
e.g. for settled historical claims, recency is weak evidence, so the `historical`
profile discounts the freshness weight and shifts it to source reliability.
"""

from eip_trust.models import ClaimType, ScoringWeights

DEFAULT_WEIGHTS = ScoringWeights(version="2026-06-19.v0")

# Historical claims: discount freshness (recency is weak/irrelevant for settled
# history), redistribute to source reliability. Component weights still sum to 1.0.
HISTORICAL_WEIGHTS = ScoringWeights(
    version="2026-06-19.v0-historical",
    source_reliability=0.35,
    corroboration=0.25,
    evidence_quality=0.20,
    independence=0.15,
    freshness=0.05,
)


def weights_for(claim_type: ClaimType | None = None, *, historical: bool = False) -> ScoringWeights:
    """Select a scoring profile.

    `historical=True` selects the freshness-discounted profile. `claim_type` is
    accepted for forward compatibility (future per-type profiles) and currently
    maps to the default unless `historical` is set. The returned config's
    `version` is recorded on every verdict for reproducibility.
    """
    if historical:
        return HISTORICAL_WEIGHTS
    return DEFAULT_WEIGHTS
