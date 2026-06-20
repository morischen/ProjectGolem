"""Graph-store seam (ADR-0006).

`GraphStore.query_candidates` returns evidence candidates reached by traversing the
knowledge graph from a claim. `Neo4jGraphStore` adapts the `neo4j` driver; tests use
a fake store. The Cypher is overridable; the default is illustrative until the graph
schema is finalized.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

DEFAULT_CYPHER = """
MATCH (c:Claim)-[:mentions]->(:Entity)<-[:mentions]-(e:Evidence)-[:reported_by]->(s:Source)
WHERE toLower(c.text) CONTAINS toLower($claim_text)
RETURN e.id AS id, s.id AS source_id, s.tier AS source_tier,
       e.content AS content, e.freshness AS freshness, 1.0 AS relevance
LIMIT $limit
""".strip()


@dataclass(frozen=True)
class GraphHit:
    id: str
    source_id: str
    source_tier: int
    content: str
    freshness: float = 0.5
    relevance: float = 1.0


@runtime_checkable
class GraphStore(Protocol):
    def query_candidates(self, claim_text: str, *, limit: int) -> list[GraphHit]: ...


class Neo4jGraphStore:
    """Adapter over a Neo4j driver. `driver` is duck-typed to neo4j's API
    (`driver.session()` / `session.run`) so this module stays import-light."""

    def __init__(self, driver: Any, *, cypher: str = DEFAULT_CYPHER) -> None:
        self._driver = driver
        self._cypher = cypher

    def query_candidates(self, claim_text: str, *, limit: int) -> list[GraphHit]:
        with self._driver.session() as session:
            result = session.run(self._cypher, claim_text=claim_text, limit=limit)
            hits: list[GraphHit] = []
            for record in result:
                freshness = record.get("freshness")
                hits.append(
                    GraphHit(
                        id=str(record["id"]),
                        source_id=str(record["source_id"]),
                        source_tier=int(record["source_tier"]),
                        content=str(record["content"]),
                        freshness=float(freshness) if freshness is not None else 0.5,
                        relevance=float(record.get("relevance", 1.0)),
                    )
                )
            return hits


def make_neo4j_store(
    uri: str, user: str, password: str, *, cypher: str = DEFAULT_CYPHER
) -> Neo4jGraphStore:
    """Build a Neo4jGraphStore against a running Neo4j (e.g. infra/docker-compose).
    Imports the driver lazily so importing this module needs no live dependency."""
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(uri, auth=(user, password))
    return Neo4jGraphStore(driver, cypher=cypher)
