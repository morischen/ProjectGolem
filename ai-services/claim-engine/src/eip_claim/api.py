"""HTTP surface for the Claim Engine (FastAPI).

`POST /v1/extract` normalizes raw text into a Claim. The LLM client is injectable
so tests can pass a `StubLLMClient` (hermetic, no network); at runtime it defaults
to `AnthropicLLMClient`. The endpoint extracts/classifies only — it never scores.

    uv run uvicorn eip_claim.api:app --reload --port 8001
"""

from __future__ import annotations

from eip_llm import AnthropicLLMClient, LLMClient
from fastapi import FastAPI
from pydantic import BaseModel

from eip_claim._generated.claim import Claim
from eip_claim.extractor import extract_claim


class ExtractRequest(BaseModel):
    text: str
    claim_id: str


def create_app(llm: LLMClient | None = None) -> FastAPI:
    engine_llm: LLMClient = llm if llm is not None else AnthropicLLMClient()
    app = FastAPI(title="EIP Claim Engine", version="0.0.1")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/extract", response_model=Claim)
    def extract(request: ExtractRequest) -> Claim:
        return extract_claim(request.text, claim_id=request.claim_id, llm=engine_llm).claim

    return app


app = create_app()
