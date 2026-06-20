"""Contract conformance tests.

These enforce that the generated/used models stay in lock-step with the JSON
Schemas in `contracts/` (the source of truth, ADR-0004): model instances must
serialize to data that validates against the schema, and the enums must match.
Drift here fails the suite regardless of any codegen quirk.
"""

import json
from pathlib import Path

import jsonschema
import pytest

from eip_trust import Evidence, EvidenceRelation, score_claim
from eip_trust.models import Claim, ClaimType, Verdict

CONTRACTS = Path(__file__).resolve().parents[3] / "contracts"


def load(name: str) -> dict:
    return json.loads((CONTRACTS / name).read_text())


def test_contracts_dir_resolves():
    assert CONTRACTS.is_dir(), f"contracts/ not found at {CONTRACTS}"


def test_evidence_model_conforms_to_schema():
    e = Evidence(
        id="e1",
        source_id="s1",
        source_tier=1,
        relation=EvidenceRelation.SUPPORTS,
        quality=1.0,
        freshness=1.0,
    )
    jsonschema.validate(instance=e.model_dump(mode="json"), schema=load("evidence.schema.json"))


def test_trustresult_conforms_to_schema():
    result = score_claim(
        [
            Evidence(
                id="s0",
                source_id="s0",
                source_tier=1,
                relation=EvidenceRelation.SUPPORTS,
                quality=1.0,
                freshness=1.0,
            )
        ]
    )
    jsonschema.validate(instance=result.model_dump(mode="json"), schema=load("verdict.schema.json"))


def test_claim_model_conforms_to_schema():
    c = Claim(id="c1", text="An example normalized claim.", claim_type=ClaimType.EMPIRICAL)
    jsonschema.validate(instance=c.model_dump(mode="json"), schema=load("claim.schema.json"))


@pytest.mark.parametrize(
    ("schema_file", "defs_key", "enum_cls"),
    [
        ("verdict.schema.json", "Verdict", Verdict),
        ("evidence.schema.json", "EvidenceRelation", EvidenceRelation),
        ("claim.schema.json", "ClaimType", ClaimType),
    ],
)
def test_enum_values_match_schema(schema_file, defs_key, enum_cls):
    schema_values = set(load(schema_file)["$defs"][defs_key]["enum"])
    model_values = {member.value for member in enum_cls}
    assert model_values == schema_values
