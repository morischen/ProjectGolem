"""HTTP surface for the Evidence Retrieval Engine (FastAPI).

`POST /v1/gather` takes a claim plus candidate sources and returns classified
`Evidence`. The LLM client is injectable (stub in tests, Anthropic at runtime).
Candidate retrieval from real backends is a later loop; for now candidates are
supplied in the request. The engine classifies relation only — it never scores.

    uv run uvicorn eip_evidence.api:app --reload --port 8002
"""

from __future__ import annotations

from eip_llm import AnthropicLLMClient, LLMClient
from fastapi import FastAPI
from pydantic import BaseModel

from eip_evidence._generated.evidence import Evidence
from eip_evidence.engine import classify_candidate
from eip_evidence.models import Candidate


class GatherRequest(BaseModel):
    claim_text: str
    candidates: list[Candidate]


def create_app(llm: LLMClient | None = None) -> FastAPI:
    engine_llm: LLMClient = llm if llm is not None else AnthropicLLMClient()
    app = FastAPI(title="EIP Evidence Engine", version="0.0.1")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/gather", response_model=list[Evidence])
    def gather_endpoint(request: GatherRequest) -> list[Evidence]:
        return [
            classify_candidate(request.claim_text, candidate, llm=engine_llm)[0]
            for candidate in request.candidates
        ]

    return app


app = create_app()
