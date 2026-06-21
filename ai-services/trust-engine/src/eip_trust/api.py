"""HTTP surface for the Trust Engine (FastAPI).

A thin transport over the deterministic scorer: it validates input and calls
`score_claim` — it does not score itself (INV-DETERMINISM). When a `claim_id` is
supplied and a verdict store is configured, each result is persisted as an
append-only, versioned snapshot (INV-TEMPORAL, ADR-0008); `/v1/claims/...` exposes
the history. The store is the impure boundary — it stamps `knowledge_time` here, not
inside the engine.

    uv run uvicorn eip_trust.api:app --reload
"""

from __future__ import annotations

import os
from datetime import UTC, datetime

from eip_persistence import VerdictRecord, VerdictStore, make_postgres_store
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from eip_trust.config import weights_for
from eip_trust.engine import score_claim
from eip_trust.models import Evidence, TrustResult


class ScoreRequest(BaseModel):
    evidence: list[Evidence] = Field(default_factory=list)
    historical: bool = Field(
        default=False, description="Select the freshness-discounted historical profile."
    )
    independence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional graph-derived independence_ratio override (ADR-0007).",
    )
    claim_id: str | None = Field(
        default=None, description="If set (and a store is configured), persist the verdict."
    )
    event_time: datetime | None = Field(
        default=None, description="When the underlying event occurred, if known."
    )


def _build_store_from_env() -> VerdictStore | None:
    dsn = os.getenv("POSTGRES_DSN")
    return make_postgres_store(dsn) if dsn else None


def create_app(store: VerdictStore | None = None) -> FastAPI:
    verdict_store: VerdictStore | None = store if store is not None else _build_store_from_env()
    app = FastAPI(title="EIP Trust Engine", version="0.0.1")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/score", response_model=TrustResult)
    def score(request: ScoreRequest) -> TrustResult:
        result = score_claim(
            request.evidence,
            weights_for(historical=request.historical),
            independence=request.independence,
        )
        if verdict_store is not None and request.claim_id:
            verdict_store.append(
                request.claim_id,
                verdict=result.verdict.value,
                score=result.score,
                weights_version=result.weights_version,
                knowledge_time=datetime.now(UTC),
                event_time=request.event_time,
                payload=result.model_dump(mode="json"),
            )
        return result

    @app.get("/v1/claims", response_model=list[VerdictRecord])
    def list_claims(limit: int = 100, offset: int = 0) -> list[VerdictRecord]:
        if verdict_store is None:
            return []
        return verdict_store.list_claims(limit=limit, offset=offset)

    @app.get("/v1/claims/{claim_id}/verdicts", response_model=list[VerdictRecord])
    def verdict_history(claim_id: str) -> list[VerdictRecord]:
        return verdict_store.history(claim_id) if verdict_store is not None else []

    @app.get("/v1/claims/{claim_id}/verdict", response_model=VerdictRecord)
    def latest_verdict(claim_id: str) -> VerdictRecord:
        record = verdict_store.latest(claim_id) if verdict_store is not None else None
        if record is None:
            raise HTTPException(status_code=404, detail="no verdict for claim")
        return record

    return app


app = create_app()
