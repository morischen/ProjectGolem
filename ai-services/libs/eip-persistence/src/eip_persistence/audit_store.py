"""Append-only audit log (ADR-0008, admin portal A2).

Records every admin mutation: who did what to which target, when, and the
before/after state. Append-only and never deleted — the tamper-evident trail behind
governance-sensitive changes (e.g. scoring-weight edits, blueprint §20). Timestamps
are caller-supplied for reproducibility (INV-REPRO).
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
)

from eip_persistence.models import AuditRecord


@runtime_checkable
class AuditStore(Protocol):
    def record(
        self,
        *,
        actor: str,
        action: str,
        target: str,
        knowledge_time: datetime,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
    ) -> AuditRecord: ...

    def list(
        self, *, limit: int = 100, offset: int = 0, target: str | None = None
    ) -> list[AuditRecord]: ...


class InMemoryAuditStore:
    def __init__(self) -> None:
        self._entries: list[AuditRecord] = []

    def record(
        self,
        *,
        actor: str,
        action: str,
        target: str,
        knowledge_time: datetime,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
    ) -> AuditRecord:
        entry = AuditRecord(
            id=len(self._entries) + 1,
            actor=actor,
            action=action,
            target=target,
            knowledge_time=knowledge_time,
            before=before,
            after=after,
        )
        self._entries.append(entry)
        return entry

    def list(
        self, *, limit: int = 100, offset: int = 0, target: str | None = None
    ) -> list[AuditRecord]:
        rows = [e for e in self._entries if target is None or e.target == target]
        rows.sort(key=lambda e: e.id, reverse=True)  # newest first
        return rows[offset : offset + limit]


_metadata = MetaData()

audit_records = Table(
    "audit_records",
    _metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("actor", String, nullable=False),
    Column("action", String, nullable=False),
    Column("target", String, nullable=False, index=True),
    Column("knowledge_time", DateTime, nullable=False),
    Column("before", JSON, nullable=True),
    Column("after", JSON, nullable=True),
)


def _to_record(row: Any) -> AuditRecord:
    return AuditRecord(
        id=int(row["id"]),
        actor=row["actor"],
        action=row["action"],
        target=row["target"],
        knowledge_time=row["knowledge_time"],
        before=dict(row["before"]) if row["before"] is not None else None,
        after=dict(row["after"]) if row["after"] is not None else None,
    )


class SqlAuditStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        _metadata.create_all(engine)

    def record(
        self,
        *,
        actor: str,
        action: str,
        target: str,
        knowledge_time: datetime,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
    ) -> AuditRecord:
        with self._engine.begin() as conn:
            current_max = conn.execute(select(func.max(audit_records.c.id))).scalar()
            new_id = int(current_max or 0) + 1
            conn.execute(
                insert(audit_records).values(
                    id=new_id,
                    actor=actor,
                    action=action,
                    target=target,
                    knowledge_time=knowledge_time,
                    before=before,
                    after=after,
                )
            )
        return AuditRecord(
            id=new_id,
            actor=actor,
            action=action,
            target=target,
            knowledge_time=knowledge_time,
            before=before,
            after=after,
        )

    def list(
        self, *, limit: int = 100, offset: int = 0, target: str | None = None
    ) -> list[AuditRecord]:
        stmt = select(audit_records)
        if target is not None:
            stmt = stmt.where(audit_records.c.target == target)
        stmt = stmt.order_by(audit_records.c.id.desc()).limit(limit).offset(offset)
        with self._engine.connect() as conn:
            rows = conn.execute(stmt).mappings().all()
        return [_to_record(row) for row in rows]
