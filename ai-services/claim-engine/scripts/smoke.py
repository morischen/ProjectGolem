"""Runtime smoke check for the Claim Engine (offline, via the stub LLM client)."""

import json

from eip_claim import StubLLMClient, extract_claim

STUB_OUTPUT = json.dumps(
    {
        "text": "Country X launched an attack on City Y on 2024-01-02.",
        "claim_type": "empirical",
        "actors": ["Country X"],
        "targets": ["City Y"],
        "events": ["attack"],
        "dates": ["2024-01-02"],
        "assertions": ["Country X attacked City Y"],
    }
)


def main() -> None:
    result = extract_claim(
        "Country X attacked City Y yesterday.",
        claim_id="smoke-1",
        llm=StubLLMClient(STUB_OUTPUT, model_id="stub"),
    )
    claim = result.claim
    assert claim.id == "smoke-1"
    assert claim.claim_type.value == "empirical"
    assert result.call.inputs["claim_id"] == "smoke-1"

    print(
        f"SMOKE OK: claim_type={claim.claim_type.value} "
        f"actors={claim.actors} model={result.call.model_id}"
    )


if __name__ == "__main__":
    main()
