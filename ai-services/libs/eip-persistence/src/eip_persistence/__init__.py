"""Bitemporal, append-only verdict persistence (ADR-0008).

Verdicts accrue versions; nothing is mutated in place (INV-TEMPORAL). Timestamps are
caller-supplied for reproducibility (INV-REPRO).
"""

from eip_persistence.models import VerdictRecord
from eip_persistence.sql_store import SqlVerdictStore, make_postgres_store
from eip_persistence.store import InMemoryVerdictStore, VerdictStore

__all__ = [
    "VerdictRecord",
    "VerdictStore",
    "InMemoryVerdictStore",
    "SqlVerdictStore",
    "make_postgres_store",
]
