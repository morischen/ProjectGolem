"""HTTP surface for the Evidence Retrieval Engine (FastAPI).

`POST /v1/gather` takes a claim and returns classified `Evidence`. Candidates can be
supplied in the request (the hermetic default), or — when a retriever is configured
(injected, or built from env: `QDRANT_URL` / `NEO4J_URI`) — retrieved server-side.
The LLM client is injectable. The engine classifies relation only; it never scores.

    QDRANT_URL=http://localhost:6333 uv run uvicorn eip_evidence.api:app --port 8002
"""

from __future__ import annotations

from eip_llm import LLMClient, LLMError, build_llm_from_env
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from eip_evidence._generated.evidence import Evidence
from eip_evidence.composite import build_retriever_from_env
from eip_evidence.engine import gather
from eip_evidence.models import Candidate
from eip_evidence.retriever import Retriever, StubRetriever


class GatherRequest(BaseModel):
    claim_text: str
    candidates: list[Candidate] = Field(default_factory=list)


def create_app(llm: LLMClient | None = None, retriever: Retriever | None = None) -> FastAPI:
    engine_llm: LLMClient = llm if llm is not None else build_llm_from_env()
    configured: Retriever | None = (
        retriever if retriever is not None else build_retriever_from_env()
    )
    app = FastAPI(title="EIP Evidence Engine", version="0.0.1")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/gather", response_model=list[Evidence])
    def gather_endpoint(request: GatherRequest) -> list[Evidence]:
        # Request-supplied candidates win; otherwise use the configured retriever.
        if request.candidates:
            active: Retriever = StubRetriever(request.candidates)
        elif configured is not None:
            active = configured
        else:
            return []
        try:
            return gather(request.claim_text, retriever=active, llm=engine_llm).evidence
        except LLMError as e:
            raise HTTPException(status_code=502, detail=f"LLM provider error: {e}") from e

    return app


app = create_app()
