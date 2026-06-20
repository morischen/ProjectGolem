"""Claim extraction: raw text -> normalized Claim (contracts/claim.schema.json).

The LLM extracts entities/events and classifies the claim type; it never assesses
truth or assigns confidence (that is the Trust Engine's deterministic job). Output
is validated against the generated Claim contract, so a malformed LLM response
fails loudly rather than propagating.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from eip_claim._generated.claim import Claim
from eip_claim.llm import LLMClient, RecordedCall

SYSTEM_PROMPT = (
    "You extract a single normalized claim from source text for an evidence platform. "
    "Return ONLY a JSON object with these keys: id, text, claim_type, actors, targets, "
    "events, locations, dates, assertions. claim_type must be one of: empirical, legal, "
    "definitional, predictive, normative. Arrays may be empty. "
    "Do NOT assess whether the claim is true and do NOT assign any score or confidence — "
    "you only normalize and classify."
)


def build_prompt(text: str, claim_id: str) -> str:
    return (
        f"Claim id: {claim_id}\nSource text:\n{text}\n\nReturn the normalized claim object as JSON."
    )


@dataclass(frozen=True)
class ExtractionResult:
    """The normalized claim plus the recorded LLM call that produced it (INV-REPRO)."""

    claim: Claim
    call: RecordedCall


def extract_claim(text: str, *, claim_id: str, llm: LLMClient) -> ExtractionResult:
    """Normalize raw `text` into a Claim using `llm`. Raises if the LLM output is
    not valid JSON or does not satisfy the Claim contract."""
    prompt = build_prompt(text, claim_id)
    call = llm.complete(
        system=SYSTEM_PROMPT,
        prompt=prompt,
        inputs={"claim_id": claim_id, "text": text},
    )
    data = json.loads(call.output)
    data.setdefault("id", claim_id)
    claim = Claim.model_validate(data)
    return ExtractionResult(claim=claim, call=call)
