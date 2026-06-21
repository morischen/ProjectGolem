"""HTTP surface for the Trust Engine (FastAPI).

A thin transport over the deterministic scorer: it validates input and calls
`score_claim` — it does not score itself (INV-DETERMINISM). When a `claim_id` is
supplied and a verdict store is configured, each result is persisted as an
append-only, versioned snapshot (INV-TEMPORAL, ADR-0008); `/v1/claims/...` exposes
the history. Scoring weights are versioned *data* read from a `ConfigStore`
(admin portal A2): `/v1/config` views them and creates new, audited versions —
never mutating a prior one (INV-REPRO). The stores are the impure boundary — they
stamp `knowledge_time` here, not inside the engine.

    uv run uvicorn eip_trust.api:app --reload
"""

from __future__ import annotations

import os
from datetime import UTC, datetime

from eip_persistence import (
    AuditRecord,
    AuditStore,
    ConfigRecord,
    ConfigStore,
    InMemoryAuditStore,
    InMemoryConfigStore,
    VerdictRecord,
    VerdictStore,
    make_postgres_store,
)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ValidationError

from eip_trust.config_service import (
    DEFAULT_PROFILE,
    HISTORICAL_PROFILE,
    active_weights,
    next_version_label,
    seed_config_store,
    weights_to_payload,
)
from eip_trust.engine import score_claim
from eip_trust.models import Evidence, ScoringWeights, TrustResult

_PROFILES = (DEFAULT_PROFILE, HISTORICAL_PROFILE)


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


class ConfigUpdateRequest(BaseModel):
    """A guarded scoring-config edit. Creates a NEW version (never mutates), validated
    by the same sum-to-1 rule as `ScoringWeights`, and recorded in the audit log."""

    profile: str = Field(default=DEFAULT_PROFILE)
    actor: str = Field(min_length=1, description="Who is making the change (audited).")
    note: str | None = Field(default=None, description="Change rationale (audited).")

    source_reliability: float = Field(ge=0.0, le=1.0)
    corroboration: float = Field(ge=0.0, le=1.0)
    evidence_quality: float = Field(ge=0.0, le=1.0)
    independence: float = Field(ge=0.0, le=1.0)
    freshness: float = Field(ge=0.0, le=1.0)
    tier_reliability: dict[int, float]
    strength_floor: float = Field(ge=0.0, le=1.0)
    mixed_conflict_threshold: float = Field(ge=0.0, le=0.5)
    verified_threshold: float = Field(ge=0.0, le=1.0)


class ProfileConfig(BaseModel):
    profile: str
    active: ConfigRecord
    versions: list[int]


class ConfigView(BaseModel):
    profiles: list[ProfileConfig]


def _build_store_from_env() -> VerdictStore | None:
    dsn = os.getenv("POSTGRES_DSN")
    return make_postgres_store(dsn) if dsn else None


def create_app(
    store: VerdictStore | None = None,
    *,
    config_store: ConfigStore | None = None,
    audit_store: AuditStore | None = None,
) -> FastAPI:
    verdict_store: VerdictStore | None = store if store is not None else _build_store_from_env()
    # Config/audit default to in-memory so the admin surface works without Postgres.
    cfg_store: ConfigStore = config_store if config_store is not None else InMemoryConfigStore()
    aud_store: AuditStore = audit_store if audit_store is not None else InMemoryAuditStore()
    seed_config_store(cfg_store, datetime.now(UTC))

    app = FastAPI(title="EIP Trust Engine", version="0.0.1")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/score", response_model=TrustResult)
    def score(request: ScoreRequest) -> TrustResult:
        weights = active_weights(cfg_store, historical=request.historical)
        result = score_claim(
            request.evidence,
            weights,
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

    @app.get("/v1/config", response_model=ConfigView)
    def get_config() -> ConfigView:
        profiles: list[ProfileConfig] = []
        for profile in _PROFILES:
            active = cfg_store.active(profile)
            if active is None:
                continue
            versions = [r.version for r in cfg_store.history(profile)]
            profiles.append(ProfileConfig(profile=profile, active=active, versions=versions))
        return ConfigView(profiles=profiles)

    @app.get("/v1/config/{profile}/history", response_model=list[ConfigRecord])
    def config_history(profile: str) -> list[ConfigRecord]:
        return cfg_store.history(profile)

    @app.post("/v1/config", response_model=ConfigRecord)
    def update_config(request: ConfigUpdateRequest) -> ConfigRecord:
        label = next_version_label(cfg_store, request.profile)
        try:
            weights = ScoringWeights(
                version=label,
                source_reliability=request.source_reliability,
                corroboration=request.corroboration,
                evidence_quality=request.evidence_quality,
                independence=request.independence,
                freshness=request.freshness,
                tier_reliability=request.tier_reliability,
                strength_floor=request.strength_floor,
                mixed_conflict_threshold=request.mixed_conflict_threshold,
                verified_threshold=request.verified_threshold,
            )
        except ValidationError as exc:
            # Sum-to-1 / range violations are caller errors, not server faults. Strip
            # pydantic's non-JSON-serializable `ctx` before returning the detail.
            detail = [
                {"loc": list(e["loc"]), "msg": e["msg"], "type": e["type"]} for e in exc.errors()
            ]
            raise HTTPException(status_code=422, detail=detail) from exc

        before = cfg_store.active(request.profile)
        now = datetime.now(UTC)
        record = cfg_store.put(
            request.profile,
            payload=weights_to_payload(weights),
            knowledge_time=now,
            actor=request.actor,
            note=request.note,
        )
        aud_store.record(
            actor=request.actor,
            action="config.update",
            target=f"config:{request.profile}",
            knowledge_time=now,
            before=before.payload if before is not None else None,
            after=record.payload,
        )
        return record

    @app.get("/v1/audit", response_model=list[AuditRecord])
    def list_audit(
        limit: int = 100, offset: int = 0, target: str | None = None
    ) -> list[AuditRecord]:
        return aud_store.list(limit=limit, offset=offset, target=target)

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
