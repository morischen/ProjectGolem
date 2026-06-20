"""Bitemporal verdict store (ADR-0008).

Append-only, versioned per claim. Timestamps are supplied by the caller — the store
never reads the clock — so it stays pure, deterministic, and reproducible.
`InMemoryVerdictStore` is the hermetic default; a Postgres adapter implements the
same protocol later.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from eip_persistence.models import VerdictRecord


@runtime_checkable
class VerdictStore(Protocol):
    def append(
        self,
        claim_id: str,
        *,
        verdict: str,
        score: float,
        weights_version: str,
        knowledge_time: datetime,
        event_time: datetime | None = None,
        payload: dict[str, Any] | None = None,
    ) -> VerdictRecord: ...

    def latest(self, claim_id: str) -> VerdictRecord | None: ...

    def history(self, claim_id: str) -> list[VerdictRecord]: ...

    def as_of(self, claim_id: str, knowledge_time: datetime) -> VerdictRecord | None: ...


class InMemoryVerdictStore:
    def __init__(self) -> None:
        self._by_claim: dict[str, list[VerdictRecord]] = {}

    def append(
        self,
        claim_id: str,
        *,
        verdict: str,
        score: float,
        weights_version: str,
        knowledge_time: datetime,
        event_time: datetime | None = None,
        payload: dict[str, Any] | None = None,
    ) -> VerdictRecord:
        records = self._by_claim.setdefault(claim_id, [])
        record = VerdictRecord(
            claim_id=claim_id,
            version=len(records) + 1,
            verdict=verdict,
            score=score,
            weights_version=weights_version,
            knowledge_time=knowledge_time,
            event_time=event_time,
            payload=dict(payload or {}),
        )
        records.append(record)
        return record

    def latest(self, claim_id: str) -> VerdictRecord | None:
        records = self._by_claim.get(claim_id)
        return records[-1] if records else None

    def history(self, claim_id: str) -> list[VerdictRecord]:
        return list(self._by_claim.get(claim_id, []))

    def as_of(self, claim_id: str, knowledge_time: datetime) -> VerdictRecord | None:
        candidates = [
            r for r in self._by_claim.get(claim_id, []) if r.knowledge_time <= knowledge_time
        ]
        return max(candidates, key=lambda r: r.version) if candidates else None
