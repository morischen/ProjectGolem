"""Neo4j graph-schema seeding (ADR-0006, ADR-0010).

The knowledge graph is a *projection* of the Postgres-canonical records (ADR-0010),
used for traversal: claims → entities → evidence → sources, plus `cites` edges
between sources that power independence/citation-laundering analysis (ADR-0007). This
module declares the node-key constraints and lookup indexes that projection needs.

All statements are idempotent (`IF NOT EXISTS`), so seeding is safe to re-run. The
statements live here (testable, dependency-free); `apply_schema` executes them
against a live driver, and `scripts/seed_graph.py` is the CLI entry point.
"""

from __future__ import annotations

from typing import Any

# Uniqueness constraints (also create backing indexes) — one per node identity.
CONSTRAINTS: list[str] = [
    "CREATE CONSTRAINT claim_id IF NOT EXISTS FOR (c:Claim) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT evidence_id IF NOT EXISTS FOR (e:Evidence) REQUIRE e.id IS UNIQUE",
    "CREATE CONSTRAINT source_id IF NOT EXISTS FOR (s:Source) REQUIRE s.id IS UNIQUE",
    "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE",
]

# Secondary indexes for the traversal/filter patterns the retriever uses.
INDEXES: list[str] = [
    "CREATE INDEX source_tier IF NOT EXISTS FOR (s:Source) ON (s.tier)",
    "CREATE INDEX evidence_freshness IF NOT EXISTS FOR (e:Evidence) ON (e.freshness)",
]

SCHEMA_STATEMENTS: list[str] = CONSTRAINTS + INDEXES


def apply_schema(driver: Any) -> int:
    """Run every schema statement against a Neo4j driver. Idempotent. Returns the
    number of statements applied. `driver` is duck-typed to neo4j's API."""
    applied = 0
    with driver.session() as session:
        for statement in SCHEMA_STATEMENTS:
            session.run(statement)
            applied += 1
    return applied
