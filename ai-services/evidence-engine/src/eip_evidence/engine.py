"""Gather evidence for a claim: retrieve candidates, then classify each one's
relation (Supports/Contradicts/Neutral/Inconclusive) via the LLM.

The LLM assigns the *relation* only — it never scores truth or confidence
(INV-DETERMINISM). Each classification is a recorded call (INV-REPRO). The emitted
`Evidence` conforms to the cross-service contract and is ready for the Trust Engine.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from eip_llm import LLMClient, RecordedCall

from eip_evidence._generated.evidence import Evidence, EvidenceRelation
from eip_evidence.models import Candidate
from eip_evidence.retriever import Retriever

SYSTEM_PROMPT = (
    "You classify how a source relates to a claim for an evidence platform. "
    'Return ONLY a JSON object: {"relation": "<value>"} where <value> is one of '
    "supports, contradicts, neutral, inconclusive. "
    "Do NOT judge whether the claim is true and do NOT assign any score or confidence."
)


def build_prompt(claim_text: str, candidate: Candidate) -> str:
    return (
        f"Claim:\n{claim_text}\n\n"
        f"Source ({candidate.source_id}):\n{candidate.content}\n\n"
        "Classify the source's relation to the claim."
    )


@dataclass(frozen=True)
class GatherResult:
    """Classified evidence plus the recorded LLM calls that produced it (INV-REPRO)."""

    evidence: list[Evidence]
    calls: list[RecordedCall]


def classify_candidate(
    claim_text: str, candidate: Candidate, *, llm: LLMClient
) -> tuple[Evidence, RecordedCall]:
    call = llm.complete(
        system=SYSTEM_PROMPT,
        prompt=build_prompt(claim_text, candidate),
        inputs={"candidate_id": candidate.id, "source_id": candidate.source_id},
    )
    relation = EvidenceRelation(json.loads(call.output)["relation"])
    evidence = Evidence(
        id=candidate.id,
        source_id=candidate.source_id,
        source_tier=candidate.source_tier,
        relation=relation,
        quality=candidate.quality,
        freshness=candidate.freshness,
    )
    return evidence, call


def gather(claim_text: str, *, retriever: Retriever, llm: LLMClient) -> GatherResult:
    """Retrieve and classify all candidate evidence for a claim."""
    evidence: list[Evidence] = []
    calls: list[RecordedCall] = []
    for candidate in retriever.retrieve(claim_text):
        item, call = classify_candidate(claim_text, candidate, llm=llm)
        evidence.append(item)
        calls.append(call)
    return GatherResult(evidence=evidence, calls=calls)
