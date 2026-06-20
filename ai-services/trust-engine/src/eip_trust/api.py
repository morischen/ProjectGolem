"""HTTP surface for the Trust Engine (FastAPI).

A thin transport layer over the deterministic scorer: it validates input and calls
`score_claim` — it does not score itself (INV-DETERMINISM). Run with:

    uv run uvicorn eip_trust.api:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from eip_trust.config import weights_for
from eip_trust.engine import score_claim
from eip_trust.models import Evidence, TrustResult


class ScoreRequest(BaseModel):
    """Request body for POST /v1/score."""

    evidence: list[Evidence] = Field(default_factory=list)
    historical: bool = Field(
        default=False, description="Select the freshness-discounted historical profile."
    )


def create_app() -> FastAPI:
    app = FastAPI(title="EIP Trust Engine", version="0.0.1")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/score", response_model=TrustResult)
    def score(request: ScoreRequest) -> TrustResult:
        return score_claim(request.evidence, weights_for(historical=request.historical))

    return app


app = create_app()
