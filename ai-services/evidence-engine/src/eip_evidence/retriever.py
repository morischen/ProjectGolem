"""Retrieval surface.

`Retriever` is the seam for fetching candidate sources for a claim. `StubRetriever`
returns preset candidates for tests/offline use. Real retrievers (multi-source,
graph/vector-backed) implement the same protocol in later loops.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from eip_evidence.models import Candidate


@runtime_checkable
class Retriever(Protocol):
    def retrieve(self, claim_text: str) -> list[Candidate]: ...


class StubRetriever:
    def __init__(self, candidates: list[Candidate]) -> None:
        self._candidates = list(candidates)

    def retrieve(self, claim_text: str) -> list[Candidate]:
        return list(self._candidates)
