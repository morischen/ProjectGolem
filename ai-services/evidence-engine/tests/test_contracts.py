"""Contract conformance: gathered Evidence validates against evidence.schema.json."""

import json
from pathlib import Path

import jsonschema

from eip_evidence import Candidate, EvidenceRelation, StubLLMClient, StubRetriever, gather

CONTRACTS = Path(__file__).resolve().parents[3] / "contracts"


def load(name: str) -> dict:
    return json.loads((CONTRACTS / name).read_text())


def test_contracts_dir_resolves():
    assert CONTRACTS.is_dir(), f"contracts/ not found at {CONTRACTS}"


def test_gathered_evidence_conforms_to_schema():
    retriever = StubRetriever(
        [Candidate(id="c1", source_id="s1", source_tier=1, content="x", quality=0.9, freshness=0.8)]
    )
    result = gather(
        "claim", retriever=retriever, llm=StubLLMClient(json.dumps({"relation": "supports"}))
    )
    schema = load("evidence.schema.json")
    for evidence in result.evidence:
        jsonschema.validate(instance=evidence.model_dump(mode="json"), schema=schema)


def test_evidence_relation_enum_matches_schema():
    schema_values = set(load("evidence.schema.json")["$defs"]["EvidenceRelation"]["enum"])
    model_values = {member.value for member in EvidenceRelation}
    assert model_values == schema_values
