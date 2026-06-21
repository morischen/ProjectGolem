"""SQL-backed verdict store (ADR-0008).

Implements `VerdictStore` over SQLAlchemy Core, so the same code runs on SQLite
(hermetic tests) and Postgres (production via infra/docker-compose). Append-only:
each `append` computes the next per-claim version inside a transaction and inserts a
new row; rows are never updated.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Engine,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    and_,
    func,
    insert,
    select,
)

from eip_persistence.models import VerdictRecord

_metadata = MetaData()

verdict_records = Table(
    "verdict_records",
    _metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("claim_id", String, nullable=False, index=True),
    Column("version", Integer, nullable=False),
    Column("verdict", String, nullable=False),
    Column("score", Float, nullable=False),
    Column("weights_version", String, nullable=False),
    Column("knowledge_time", DateTime, nullable=False),
    Column("event_time", DateTime, nullable=True),
    Column("payload", JSON, nullable=False, default=dict),
    UniqueConstraint("claim_id", "version", name="uq_claim_version"),
)


def _to_record(row: Any) -> VerdictRecord:
    return VerdictRecord(
        claim_id=row["claim_id"],
        version=int(row["version"]),
        verdict=row["verdict"],
        score=float(row["score"]),
        weights_version=row["weights_version"],
        knowledge_time=row["knowledge_time"],
        event_time=row["event_time"],
        payload=dict(row["payload"] or {}),
    )


class SqlVerdictStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        _metadata.create_all(engine)

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
        data = dict(payload or {})
        with self._engine.begin() as conn:
            current_max = conn.execute(
                select(func.max(verdict_records.c.version)).where(
                    verdict_records.c.claim_id == claim_id
                )
            ).scalar()
            version = int(current_max or 0) + 1
            conn.execute(
                insert(verdict_records).values(
                    claim_id=claim_id,
                    version=version,
                    verdict=verdict,
                    score=score,
                    weights_version=weights_version,
                    knowledge_time=knowledge_time,
                    event_time=event_time,
                    payload=data,
                )
            )
        return VerdictRecord(
            claim_id=claim_id,
            version=version,
            verdict=verdict,
            score=score,
            weights_version=weights_version,
            knowledge_time=knowledge_time,
            event_time=event_time,
            payload=data,
        )

    def latest(self, claim_id: str) -> VerdictRecord | None:
        stmt = (
            select(verdict_records)
            .where(verdict_records.c.claim_id == claim_id)
            .order_by(verdict_records.c.version.desc())
            .limit(1)
        )
        with self._engine.connect() as conn:
            row = conn.execute(stmt).mappings().first()
        return _to_record(row) if row is not None else None

    def history(self, claim_id: str) -> list[VerdictRecord]:
        stmt = (
            select(verdict_records)
            .where(verdict_records.c.claim_id == claim_id)
            .order_by(verdict_records.c.version.asc())
        )
        with self._engine.connect() as conn:
            rows = conn.execute(stmt).mappings().all()
        return [_to_record(row) for row in rows]

    def list_claims(self, *, limit: int = 100, offset: int = 0) -> list[VerdictRecord]:
        latest = (
            select(
                verdict_records.c.claim_id,
                func.max(verdict_records.c.version).label("v"),
            )
            .group_by(verdict_records.c.claim_id)
            .subquery()
        )
        stmt = (
            select(verdict_records)
            .join(
                latest,
                and_(
                    verdict_records.c.claim_id == latest.c.claim_id,
                    verdict_records.c.version == latest.c.v,
                ),
            )
            .order_by(verdict_records.c.knowledge_time.desc())
            .limit(limit)
            .offset(offset)
        )
        with self._engine.connect() as conn:
            rows = conn.execute(stmt).mappings().all()
        return [_to_record(row) for row in rows]

    def as_of(self, claim_id: str, knowledge_time: datetime) -> VerdictRecord | None:
        stmt = (
            select(verdict_records)
            .where(
                verdict_records.c.claim_id == claim_id,
                verdict_records.c.knowledge_time <= knowledge_time,
            )
            .order_by(verdict_records.c.version.desc())
            .limit(1)
        )
        with self._engine.connect() as conn:
            row = conn.execute(stmt).mappings().first()
        return _to_record(row) if row is not None else None


def make_postgres_store(dsn: str) -> SqlVerdictStore:
    """Build a SqlVerdictStore against Postgres (e.g. infra/docker-compose), e.g.
    `postgresql+psycopg://eip:devpassword@localhost:5432/eip`."""
    from sqlalchemy import create_engine

    return SqlVerdictStore(create_engine(dsn))
