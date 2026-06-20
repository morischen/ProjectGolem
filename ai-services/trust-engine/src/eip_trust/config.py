"""Versioned default scoring configuration.

Weight/threshold changes are governance events: bump the version string so that
historical verdicts remain reproducible against the config that produced them.
"""

from eip_trust.models import ScoringWeights

DEFAULT_WEIGHTS = ScoringWeights(version="2026-06-19.v0")
