"""Tests for the Neo4j graph-schema seeding (idempotent statements + apply)."""

from eip_evidence.graph_schema import (
    CONSTRAINTS,
    INDEXES,
    SCHEMA_STATEMENTS,
    apply_schema,
)


class _FakeSession:
    def __init__(self, sink: list[str]) -> None:
        self._sink = sink

    def __enter__(self) -> "_FakeSession":
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def run(self, statement: str, **_: object) -> None:
        self._sink.append(statement)


class _FakeDriver:
    def __init__(self) -> None:
        self.statements: list[str] = []

    def session(self) -> _FakeSession:
        return _FakeSession(self.statements)


def test_statements_are_present_and_idempotent():
    assert SCHEMA_STATEMENTS == CONSTRAINTS + INDEXES
    assert len(SCHEMA_STATEMENTS) >= 4
    # Idempotency is what makes re-seeding safe.
    assert all("IF NOT EXISTS" in s for s in SCHEMA_STATEMENTS)
    assert all(s.startswith("CREATE ") for s in SCHEMA_STATEMENTS)


def test_apply_schema_runs_every_statement():
    driver = _FakeDriver()
    applied = apply_schema(driver)
    assert applied == len(SCHEMA_STATEMENTS)
    assert driver.statements == SCHEMA_STATEMENTS
