"""Versioned configuration store (ADR-0008, admin portal A2).

Append-only, versioned per profile (e.g. 'default', 'historical'). A methodology
change creates a new version; prior versions are never mutated, so historical
verdicts stay reproducible against the config that produced them (INV-REPRO /
INV-TEMPORAL). Timestamps are caller-supplied — the store never reads the clock.
The store is schema-agnostic: payload shape (e.g. ScoringWeights) is owned by the
consuming service.
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
    UniqueConstraint,
    func,
    insert,
    select,
)

from eip_persistence.models import ConfigRecord


@runtime_checkable
class ConfigStore(Protocol):
    def put(
        self,
        profile: str,
        *,
        payload: dict[str, Any],
        knowledge_time: datetime,
        actor: str | None = None,
        note: str | None = None,
    ) -> ConfigRecord: ...

    def active(self, profile: str) -> ConfigRecord | None: ...

    def history(self, profile: str) -> list[ConfigRecord]: ...

    def version(self, profile: str, version: int) -> ConfigRecord | None: ...

    def profiles(self) -> list[str]: ...


class InMemoryConfigStore:
    def __init__(self) -> None:
        self._by_profile: dict[str, list[ConfigRecord]] = {}

    def put(
        self,
        profile: str,
        *,
        payload: dict[str, Any],
        knowledge_time: datetime,
        actor: str | None = None,
        note: str | None = None,
    ) -> ConfigRecord:
        versions = self._by_profile.setdefault(profile, [])
        record = ConfigRecord(
            profile=profile,
            version=len(versions) + 1,
            payload=dict(payload),
            knowledge_time=knowledge_time,
            actor=actor,
            note=note,
        )
        versions.append(record)
        return record

    def active(self, profile: str) -> ConfigRecord | None:
        versions = self._by_profile.get(profile)
        return versions[-1] if versions else None

    def history(self, profile: str) -> list[ConfigRecord]:
        return list(self._by_profile.get(profile, []))

    def version(self, profile: str, version: int) -> ConfigRecord | None:
        for record in self._by_profile.get(profile, []):
            if record.version == version:
                return record
        return None

    def profiles(self) -> list[str]:
        return sorted(self._by_profile)


_metadata = MetaData()

config_records = Table(
    "config_records",
    _metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("profile", String, nullable=False, index=True),
    Column("version", Integer, nullable=False),
    Column("payload", JSON, nullable=False),
    Column("knowledge_time", DateTime, nullable=False),
    Column("actor", String, nullable=True),
    Column("note", String, nullable=True),
    UniqueConstraint("profile", "version", name="uq_config_profile_version"),
)


def _to_record(row: Any) -> ConfigRecord:
    return ConfigRecord(
        profile=row["profile"],
        version=int(row["version"]),
        payload=dict(row["payload"] or {}),
        knowledge_time=row["knowledge_time"],
        actor=row["actor"],
        note=row["note"],
    )


class SqlConfigStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        _metadata.create_all(engine)

    def put(
        self,
        profile: str,
        *,
        payload: dict[str, Any],
        knowledge_time: datetime,
        actor: str | None = None,
        note: str | None = None,
    ) -> ConfigRecord:
        data = dict(payload)
        with self._engine.begin() as conn:
            current_max = conn.execute(
                select(func.max(config_records.c.version)).where(
                    config_records.c.profile == profile
                )
            ).scalar()
            version = int(current_max or 0) + 1
            conn.execute(
                insert(config_records).values(
                    profile=profile,
                    version=version,
                    payload=data,
                    knowledge_time=knowledge_time,
                    actor=actor,
                    note=note,
                )
            )
        return ConfigRecord(
            profile=profile,
            version=version,
            payload=data,
            knowledge_time=knowledge_time,
            actor=actor,
            note=note,
        )

    def active(self, profile: str) -> ConfigRecord | None:
        stmt = (
            select(config_records)
            .where(config_records.c.profile == profile)
            .order_by(config_records.c.version.desc())
            .limit(1)
        )
        with self._engine.connect() as conn:
            row = conn.execute(stmt).mappings().first()
        return _to_record(row) if row is not None else None

    def history(self, profile: str) -> list[ConfigRecord]:
        stmt = (
            select(config_records)
            .where(config_records.c.profile == profile)
            .order_by(config_records.c.version.asc())
        )
        with self._engine.connect() as conn:
            rows = conn.execute(stmt).mappings().all()
        return [_to_record(row) for row in rows]

    def version(self, profile: str, version: int) -> ConfigRecord | None:
        stmt = select(config_records).where(
            config_records.c.profile == profile,
            config_records.c.version == version,
        )
        with self._engine.connect() as conn:
            row = conn.execute(stmt).mappings().first()
        return _to_record(row) if row is not None else None

    def profiles(self) -> list[str]:
        stmt = select(config_records.c.profile).distinct().order_by(config_records.c.profile)
        with self._engine.connect() as conn:
            return [row[0] for row in conn.execute(stmt).all()]
