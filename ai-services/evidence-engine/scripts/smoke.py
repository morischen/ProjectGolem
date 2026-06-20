"""Runtime smoke check for the Evidence Retrieval Engine (offline, stub clients)."""

import json

from eip_evidence import Candidate, StubLLMClient, StubRetriever, gather


def main() -> None:
    retriever = StubRetriever(
        [
            Candidate(
                id="e1",
                source_id="court-1",
                source_tier=1,
                content="...",
                quality=0.95,
                freshness=0.9,
            ),
            Candidate(
                id="e2", source_id="ngo-1", source_tier=3, content="...", quality=0.6, freshness=0.7
            ),
        ]
    )
    llm = StubLLMClient(
        [json.dumps({"relation": "supports"}), json.dumps({"relation": "contradicts"})]
    )
    result = gather("An example claim.", retriever=retriever, llm=llm)

    assert len(result.evidence) == 2
    assert len(result.calls) == 2
    relations = [e.relation.value for e in result.evidence]

    print(f"SMOKE OK: gathered {len(result.evidence)} evidence, relations={relations}")


if __name__ == "__main__":
    main()
