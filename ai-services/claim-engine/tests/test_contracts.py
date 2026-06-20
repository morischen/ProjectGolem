"""Contract conformance: extracted Claim objects validate against claim.schema.json."""

import json
from pathlib import Path

import jsonschema

from eip_claim import Claim, ClaimType, StubLLMClient, extract_claim

CONTRACTS = Path(__file__).resolve().parents[3] / "contracts"


def load(name: str) -> dict:
    return json.loads((CONTRACTS / name).read_text())


def test_contracts_dir_resolves():
    assert CONTRACTS.is_dir(), f"contracts/ not found at {CONTRACTS}"


def test_extracted_claim_conforms_to_schema():
    out = json.dumps({"text": "An example claim.", "claim_type": "empirical"})
    result = extract_claim("An example claim.", claim_id="c1", llm=StubLLMClient(out))
    jsonschema.validate(
        instance=result.claim.model_dump(mode="json"),
        schema=load("claim.schema.json"),
    )


def test_claim_type_enum_matches_schema():
    schema_values = set(load("claim.schema.json")["$defs"]["ClaimType"]["enum"])
    model_values = {member.value for member in ClaimType}
    assert model_values == schema_values


def test_claim_model_importable():
    assert Claim.__name__ == "Claim"
