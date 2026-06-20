"""Independence / citation-laundering analysis (ADR-0007; review §4).

Apparent corroboration can be an illusion: many "independent" sources that all trace
to one origin, or citation cycles, are really a *single* independent voice. This
groups sources by shared provenance (weakly-connected components over the citation
graph) so downstream scoring isn't fooled by laundered corroboration.

Pure function, no I/O — the citation edges come from the knowledge graph (Neo4j) in
real use, but the analysis itself is deterministic and dependency-free.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class IndependenceReport:
    distinct_sources: int
    independent_groups: int
    independence_ratio: float
    groups: list[list[str]]


def assess_independence(
    source_ids: Iterable[str],
    citations: Iterable[tuple[str, str]],
) -> IndependenceReport:
    """Group sources by shared provenance.

    A citation `(a, b)` means source `a` cites / derives from `b`, so they belong to
    the same provenance cluster. Sources in the same weakly-connected component are
    NOT independent corroborations (shared origin or citation cycle).
    `independence_ratio = independent_groups / distinct_sources` — 1.0 means every
    source is its own independent voice; lower means corroboration is laundered.
    """
    parent: dict[str, str] = {}

    def find(node: str) -> str:
        parent.setdefault(node, node)
        root = node
        while parent[root] != root:
            root = parent[root]
        while parent[node] != root:  # path compression
            parent[node], node = root, parent[node]
        return root

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    sources = set(source_ids)
    for source in sources:
        find(source)
    for citer, cited in citations:
        union(citer, cited)

    roots_with_sources = {find(s) for s in sources}
    clusters: dict[str, list[str]] = {}
    for node in parent:
        root = find(node)
        if root in roots_with_sources:
            clusters.setdefault(root, []).append(node)

    groups = sorted(sorted(members) for members in clusters.values())
    distinct = len(sources)
    independent_groups = len(groups)
    ratio = independent_groups / distinct if distinct else 1.0

    return IndependenceReport(
        distinct_sources=distinct,
        independent_groups=independent_groups,
        independence_ratio=ratio,
        groups=groups,
    )
