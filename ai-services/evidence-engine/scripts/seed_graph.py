"""Seed the Neo4j graph schema (constraints + indexes).

Idempotent — safe to re-run. Reads connection settings from the environment
(NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD), e.g. against infra/docker-compose:

    NEO4J_URI=bolt://localhost:7687 NEO4J_USER=neo4j NEO4J_PASSWORD=devpassword \
        uv run python scripts/seed_graph.py

With `--dry-run` (or no NEO4J_URI) it just prints the statements it would apply,
so the script is useful and inspectable without a live database.
"""

from __future__ import annotations

import os
import sys

from eip_evidence.graph_schema import SCHEMA_STATEMENTS, apply_schema


def main() -> int:
    dry_run = "--dry-run" in sys.argv or not os.getenv("NEO4J_URI")
    if dry_run:
        print(f"# dry run — {len(SCHEMA_STATEMENTS)} schema statements:")
        for stmt in SCHEMA_STATEMENTS:
            print(stmt + ";")
        return 0

    from eip_evidence.graphstore import make_neo4j_store

    store = make_neo4j_store(
        os.environ["NEO4J_URI"],
        os.environ.get("NEO4J_USER", "neo4j"),
        os.environ.get("NEO4J_PASSWORD", ""),
    )
    applied = apply_schema(store._driver)  # noqa: SLF001 — script owns the driver
    print(f"applied {applied} schema statements")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
