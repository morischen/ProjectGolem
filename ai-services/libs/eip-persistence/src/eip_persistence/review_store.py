"""Human-review queue store (ADR-0008, admin portal A3).

Holds items that need a human: low-confidence verdicts, evidence conflicts, and
public appeals (FR-007). Unlike the append-only verdict/config stores, a review item
is operational state — it opens, then resolves. The store mutates the item's status
on resolution; the durable record of what a resolution *did* (an override → a new
verdict version; an audit entry) lives in the verdict store and audit log. Timestamps
are caller-supplied (INV-REPRO).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Engine,
    Integer,
    MetaData,
    String,
    Table,
    func,
    insert,
    select,
    update,
)

from eip_persistence.models import ReviewRecord

OPEN = "open"
RESOLVED = "resolved"


@runtime_checkable
class ReviewStore(Protocol):
    def open_item(
        self,
        claim_id: str,
        *,
        kind: str,
        created_time: datetime,
        detail: dict[str, Any] | None = None,
    ) -> ReviewRecord: ...

    def get(self, item_id: int) -> ReviewRecord | None: ...

    def list(
        self, *, status: str | None = None, limit: int = 100, offset: int = 0
    ) -> list[ReviewRecord]: ...

    def resolve(
        self, item_id: int, *, resolution: dict[str, Any], resolved_time: datetime
    ) -> ReviewRecord | None: ...


class InMemoryReviewStore:
    def __init__(self) -> None:
        self._items: dict[int, ReviewRecord] = {}
        self._seq = 0

    def open_item(
        self,
        claim_id: str,
        *,
        kind: str,
        created_time: datetime,
        detail: dict[str, Any] | None = None,
    ) -> ReviewRecord:
        self._seq += 1
        record = ReviewRecord(
            id=self._seq,
            claim_id=claim_id,
            kind=kind,
            status=OPEN,
            created_time=created_time,
            detail=dict(detail or {}),
        )
        self._items[record.id] = record
        return record

    def get(self, item_id: int) -> ReviewRecord | None:
        return self._items.get(item_id)

    def list(
        self, *, status: str | None = None, limit: int = 100, offset: int = 0
    ) -> list[ReviewRecord]:
        rows = [r for r in self._items.values() if status is None or r.status == status]
        rows.sort(key=lambda r: r.id, reverse=True)  # newest first
        return rows[offset : offset + limit]

    def resolve(
        self, item_id: int, *, resolution: dict[str, Any], resolved_time: datetime
    ) -> ReviewRecord | None:
        existing = self._items.get(item_id)
        if existing is None:
            return None
        resolved = existing.model_copy(
            update={
                "status": RESOLVED,
                "resolution": dict(resolution),
                "resolved_time": resolved_time,
            }
        )
        self._items[item_id] = resolved
        return resolved


_metadata = MetaData()

review_items = Table(
    "review_items",
    _metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("claim_id", String, nullable=False, index=True),
    Column("kind", String, nullable=False),
    Column("status", String, nullable=False, index=True),
    Column("created_time", DateTime, nullable=False),
    Column("detail", JSON, nullable=False, default=dict),
    Column("resolution", JSON, nullable=True),
    Column("resolved_time", DateTime, nullable=True),
)


def _to_record(row: Any) -> ReviewRecord:
    return ReviewRecord(
        id=int(row["id"]),
        claim_id=row["claim_id"],
        kind=row["kind"],
        status=row["status"],
        created_time=row["created_time"],
        detail=dict(row["detail"] or {}),
        resolution=dict(row["resolution"]) if row["resolution"] is not None else None,
        resolved_time=row["resolved_time"],
    )


class SqlReviewStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        _metadata.create_all(engine)

    def open_item(
        self,
        claim_id: str,
        *,
        kind: str,
        created_time: datetime,
        detail: dict[str, Any] | None = None,
    ) -> ReviewRecord:
        data = dict(detail or {})
        with self._engine.begin() as conn:
            current_max = conn.execute(select(func.max(review_items.c.id))).scalar()
            new_id = int(current_max or 0) + 1
            conn.execute(
                insert(review_items).values(
                    id=new_id,
                    claim_id=claim_id,
                    kind=kind,
                    status=OPEN,
                    created_time=created_time,
                    detail=data,
                    resolution=None,
                    resolved_time=None,
                )
            )
        return ReviewRecord(
            id=new_id,
            claim_id=claim_id,
            kind=kind,
            status=OPEN,
            created_time=created_time,
            detail=data,
        )

    def get(self, item_id: int) -> ReviewRecord | None:
        with self._engine.connect() as conn:
            row = (
                conn.execute(select(review_items).where(review_items.c.id == item_id))
                .mappings()
                .first()
            )
        return _to_record(row) if row is not None else None

    def list(
        self, *, status: str | None = None, limit: int = 100, offset: int = 0
    ) -> list[ReviewRecord]:
        stmt = select(review_items)
        if status is not None:
            stmt = stmt.where(review_items.c.status == status)
        stmt = stmt.order_by(review_items.c.id.desc()).limit(limit).offset(offset)
        with self._engine.connect() as conn:
            rows = conn.execute(stmt).mappings().all()
        return [_to_record(row) for row in rows]

    def resolve(
        self, item_id: int, *, resolution: dict[str, Any], resolved_time: datetime
    ) -> ReviewRecord | None:
        with self._engine.begin() as conn:
            result = conn.execute(
                update(review_items)
                .where(review_items.c.id == item_id)
                .values(
                    status=RESOLVED,
                    resolution=dict(resolution),
                    resolved_time=resolved_time,
                )
            )
            if result.rowcount == 0:
                return None
        return self.get(item_id)
