"""Bridge between the Trust Engine's `ScoringWeights` and the versioned `ConfigStore`.

The store (eip-persistence) is schema-agnostic — it holds opaque JSON payloads. This
module owns the `ScoringWeights` shape: it serializes weights to/from store payloads,
seeds the store from the built-in profiles, and resolves the *active* weights for a
profile. Methodology changes create a new config version (never mutate a prior one),
so verdicts stay reproducible against the config that produced them (INV-REPRO).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from eip_persistence import ConfigStore

from eip_trust.config import DEFAULT_WEIGHTS, HISTORICAL_WEIGHTS
from eip_trust.models import ScoringWeights

DEFAULT_PROFILE = "default"
HISTORICAL_PROFILE = "historical"

_SEED = {DEFAULT_PROFILE: DEFAULT_WEIGHTS, HISTORICAL_PROFILE: HISTORICAL_WEIGHTS}


def weights_to_payload(weights: ScoringWeights) -> dict[str, Any]:
    """Serialize weights to a JSON-safe store payload (int tier keys → strings)."""
    return weights.model_dump(mode="json")


def weights_from_payload(payload: dict[str, Any]) -> ScoringWeights:
    """Rebuild `ScoringWeights` from a stored payload. Re-runs the sum-to-1 validator;
    pydantic coerces the JSON string tier keys back to ints."""
    return ScoringWeights(**payload)


def seed_config_store(store: ConfigStore, knowledge_time: datetime) -> None:
    """Seed the built-in profiles into an empty store; no-op for profiles already set.
    Idempotent so it is safe to call on every startup."""
    for profile, weights in _SEED.items():
        if store.active(profile) is None:
            store.put(
                profile,
                payload=weights_to_payload(weights),
                knowledge_time=knowledge_time,
                actor="system",
                note="seed from built-in profile",
            )


def active_weights(store: ConfigStore | None, *, historical: bool = False) -> ScoringWeights:
    """Resolve the active weights for the selected profile. Falls back to the built-in
    constants when no store is configured or the profile is unseeded."""
    profile = HISTORICAL_PROFILE if historical else DEFAULT_PROFILE
    if store is not None:
        record = store.active(profile)
        if record is not None:
            return weights_from_payload(record.payload)
    return _SEED[profile]


def next_version_label(store: ConfigStore | None, profile: str) -> str:
    """A deterministic, traceable version string for the next config version of a
    profile, e.g. 'default.v3'. Recorded on verdicts as `weights_version`."""
    current = store.active(profile) if store is not None else None
    n = (current.version + 1) if current is not None else 1
    return f"{profile}.v{n}"
