"""End-to-end: claim -> evidence -> trust, across the three engines in one process.

Evidence crosses package boundaries as JSON (the real HTTP boundary), which proves
the independently-generated contracts in each service actually line up. The LLM and
retriever are stubbed, so this is hermetic and deterministic.
"""

import json

from eip_claim import extract_claim
from eip_evidence import Candidate, StubRetriever, gather
from eip_evidence import EvidenceRelation as EvidenceRelationFromEvidence
from eip_llm import StubLLMClient
from eip_trust import Evidence as TrustEvidence
from eip_trust import EvidenceRelation as EvidenceRelationFromTrust
from eip_trust import Verdict, score_claim

CLAIM_TEXT = "Country X attacked City Y on 2024-01-02."
CLAIM_JSON = json.dumps(
    {"text": CLAIM_TEXT, "claim_type": "empirical", "actors": ["Country X"], "targets": ["City Y"]}
)


def _candidates(n: int) -> list[Candidate]:
    return [
        Candidate(
            id=f"e{i}",
            source_id=f"s{i}",
            source_tier=1,
            content=f"source {i}",
            quality=1.0,
            freshness=1.0,
        )
        for i in range(n)
    ]


def _to_trust_evidence(gather_result) -> list[TrustEvidence]:
    # Re-validate each evidence item through the Trust Engine's own contract model,
    # exactly as it would arrive over HTTP as JSON.
    return [TrustEvidence.model_validate(e.model_dump(mode="json")) for e in gather_result.evidence]


def test_supported_claim_runs_through_to_verified():
    claim = extract_claim(CLAIM_TEXT, claim_id="c1", llm=StubLLMClient(CLAIM_JSON)).claim
    assert claim.claim_type.value == "empirical"

    gathered = gather(
        claim.text,
        retriever=StubRetriever(_candidates(3)),
        llm=StubLLMClient([json.dumps({"relation": "supports"})] * 3),
    )
    result = score_claim(_to_trust_evidence(gathered))

    assert result.verdict is Verdict.VERIFIED
    assert result.relevant_count == 3
    assert result.supporting_count == 3


def test_conflicting_evidence_runs_through_to_mixed():
    claim = extract_claim(CLAIM_TEXT, claim_id="c2", llm=StubLLMClient(CLAIM_JSON)).claim
    gathered = gather(
        claim.text,
        retriever=StubRetriever(_candidates(4)),
        llm=StubLLMClient(
            [
                json.dumps({"relation": r})
                for r in ("supports", "supports", "contradicts", "contradicts")
            ]
        ),
    )
    result = score_claim(_to_trust_evidence(gathered))
    assert result.verdict is Verdict.MIXED_EVIDENCE


def test_evidence_relation_contract_is_identical_across_engines():
    # The two engines generate their own EvidenceRelation from the same schema —
    # the values must match, or JSON round-tripping evidence between them would break.
    assert {r.value for r in EvidenceRelationFromEvidence} == {
        r.value for r in EvidenceRelationFromTrust
    }
