"""Calibration harness — run the LLM over labeled claims and measure accuracy.

Combines evidence-engine classification (the LLM's job) with trust-engine scoring,
exchanging Evidence as JSON across the package boundary. Pure over an injected
`llm`: hermetic with `StubLLMClient`, live with `build_llm_from_env()`. This is the
seam for §28 calibration once a labeled source-level dataset exists.
"""

from __future__ import annotations

from dataclasses import dataclass

from eip_evidence import Candidate, StubRetriever, gather
from eip_llm import LLMClient
from eip_trust import Evidence as TrustEvidence
from eip_trust import score_claim


@dataclass(frozen=True)
class CalibrationItem:
    claim_text: str
    candidate: Candidate
    expected_relation: str
    expected_verdict: str


@dataclass(frozen=True)
class CalibrationReport:
    total: int
    relation_accuracy: float
    verdict_accuracy: float


def _to_trust(evidence: object) -> TrustEvidence:
    return TrustEvidence.model_validate(evidence.model_dump(mode="json"))  # type: ignore[attr-defined]


def run_calibration(items: list[CalibrationItem], *, llm: LLMClient) -> CalibrationReport:
    """Classify each item's candidate with `llm`, score it, and compare relation +
    verdict against the labels."""
    relation_hits = 0
    verdict_hits = 0
    for item in items:
        result = gather(item.claim_text, retriever=StubRetriever([item.candidate]), llm=llm)
        evidence = result.evidence[0]
        if evidence.relation.value == item.expected_relation:
            relation_hits += 1
        verdict = score_claim([_to_trust(e) for e in result.evidence]).verdict
        if verdict.value == item.expected_verdict:
            verdict_hits += 1
    n = len(items)
    return CalibrationReport(
        total=n,
        relation_accuracy=relation_hits / n if n else 0.0,
        verdict_accuracy=verdict_hits / n if n else 0.0,
    )
