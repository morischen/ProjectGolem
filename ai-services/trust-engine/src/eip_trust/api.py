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
    CalibrationRunRecord,
    CalibrationStore,
    ConfigRecord,
    ConfigStore,
    InMemoryAuditStore,
    InMemoryCalibrationStore,
    InMemoryConfigStore,
    InMemoryReviewStore,
    ReviewRecord,
    ReviewStore,
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
from eip_trust.metrics import benchmark_metrics, compute_metrics
from eip_trust.models import Evidence, ScoringWeights, TrustResult, Verdict
from eip_trust.proposals import ConfigProposal, InMemoryProposalStore, ProposalError

_PROFILES = (DEFAULT_PROFILE, HISTORICAL_PROFILE)

# A verdict whose confidence is below this is queued for human review (FR-007).
LOW_CONFIDENCE_THRESHOLD = 0.70

_VALID_VERDICTS = {v.value for v in Verdict}
_DECISIONS = {"upheld", "override", "dismissed"}
_APPEAL_TYPES = {"new_evidence", "source_challenge", "methodology"}


def _needs_review(result: TrustResult) -> str | None:
    """Classify whether a fresh verdict should be escalated, and why (FR-007)."""
    if result.verdict is Verdict.MIXED_EVIDENCE:
        return "evidence_conflict"
    if result.score < LOW_CONFIDENCE_THRESHOLD:
        return "low_confidence"
    return None


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


class ApprovalRequest(BaseModel):
    approver: str = Field(min_length=1, description="Who is approving (must be distinct).")


class ProfileConfig(BaseModel):
    profile: str
    active: ConfigRecord
    versions: list[int]


class ConfigView(BaseModel):
    profiles: list[ProfileConfig]


class ReviewResolveRequest(BaseModel):
    """A reviewer's decision on a queued item (INV-OVERRIDE). An 'override' appends a
    new, reviewer-attributed verdict version — never mutating a prior one."""

    reviewer: str = Field(min_length=1, description="Who is resolving the item (audited).")
    decision: str = Field(description="'upheld' | 'override' | 'dismissed'.")
    note: str | None = Field(default=None, description="Reviewer rationale (audited).")
    override_verdict: str | None = Field(
        default=None, description="Required when decision='override'; one of the six verdicts."
    )
    override_score: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Optional confidence to record with an override."
    )
    event_time: datetime | None = Field(default=None)


class AppealRequest(BaseModel):
    """A public challenge to a verdict (logged publicly). Lands in the review queue."""

    claim_id: str = Field(min_length=1)
    appeal_type: str = Field(description="'new_evidence' | 'source_challenge' | 'methodology'.")
    body: str = Field(min_length=1, description="The substance of the appeal.")
    submitter: str | None = Field(default=None, description="Optional submitter identity.")


class ClaimIntakeRequest(BaseModel):
    """A public proposal that a claim be assessed. Lands in the review queue for
    triage — it does not itself score (assessment is an authenticated operation)."""

    text: str = Field(min_length=1, description="The claim a member of the public submits.")
    submitter: str | None = Field(default=None, description="Optional submitter identity.")


class AuditCreateRequest(BaseModel):
    """Record an admin action in the central audit log (e.g. from the gateway)."""

    actor: str = Field(min_length=1)
    action: str = Field(min_length=1)
    target: str = Field(min_length=1)
    before: dict[str, object] | None = None
    after: dict[str, object] | None = None


class BenchmarkMetrics(BaseModel):
    total: int
    verdict_accuracy: float
    calibration_error: float
    by_difficulty: dict[str, float]


class QueueHealth(BaseModel):
    open: int
    resolved: int
    by_kind: dict[str, int]


class MetricsView(BaseModel):
    benchmark: BenchmarkMetrics | None
    queue: QueueHealth
    claims_count: int


def _build_store_from_env() -> VerdictStore | None:
    dsn = os.getenv("POSTGRES_DSN")
    return make_postgres_store(dsn) if dsn else None


def _weights_from_request(label: str, request: ConfigUpdateRequest) -> ScoringWeights:
    """Validate a config edit into ScoringWeights (sum-to-1 + ranges). Raises
    HTTPException(422) on a caller error, with pydantic's non-serializable ctx stripped."""
    try:
        return ScoringWeights(
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
        detail = [{"loc": list(e["loc"]), "msg": e["msg"], "type": e["type"]} for e in exc.errors()]
        raise HTTPException(status_code=422, detail=detail) from exc


def create_app(
    store: VerdictStore | None = None,
    *,
    config_store: ConfigStore | None = None,
    audit_store: AuditStore | None = None,
    review_store: ReviewStore | None = None,
    calibration_store: CalibrationStore | None = None,
) -> FastAPI:
    verdict_store: VerdictStore | None = store if store is not None else _build_store_from_env()
    # Config/audit/review/calibration default to in-memory so the admin surface works
    # without Postgres.
    cfg_store: ConfigStore = config_store if config_store is not None else InMemoryConfigStore()
    aud_store: AuditStore = audit_store if audit_store is not None else InMemoryAuditStore()
    rev_store: ReviewStore = review_store if review_store is not None else InMemoryReviewStore()
    cal_store: CalibrationStore = (
        calibration_store if calibration_store is not None else InMemoryCalibrationStore()
    )
    proposal_store = InMemoryProposalStore()
    # Approvals required before a proposed config change applies (separation of duties).
    required_approvals = max(1, int(os.getenv("CONFIG_REQUIRED_APPROVALS", "2")))
    seed_config_store(cfg_store, datetime.now(UTC))

    def _has_open_item(claim_id: str) -> bool:
        return any(item.claim_id == claim_id for item in rev_store.list(status="open"))

    def _apply_config(
        profile: str, payload: dict[str, object], actor: str, note: str | None
    ) -> ConfigRecord:
        """Write a new config version + audit entry. Shared by direct edits and
        approved proposals."""
        before = cfg_store.active(profile)
        now = datetime.now(UTC)
        record = cfg_store.put(profile, payload=payload, knowledge_time=now, actor=actor, note=note)
        aud_store.record(
            actor=actor,
            action="config.update",
            target=f"config:{profile}",
            knowledge_time=now,
            before=before.payload if before is not None else None,
            after=record.payload,
        )
        return record

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
            now = datetime.now(UTC)
            verdict_store.append(
                request.claim_id,
                verdict=result.verdict.value,
                score=result.score,
                weights_version=result.weights_version,
                knowledge_time=now,
                event_time=request.event_time,
                payload=result.model_dump(mode="json"),
            )
            # Escalate low-confidence / conflicted verdicts (FR-007), one open item
            # per claim at a time so re-scoring doesn't flood the queue.
            kind = _needs_review(result)
            if kind is not None and not _has_open_item(request.claim_id):
                rev_store.open_item(
                    request.claim_id,
                    kind=kind,
                    created_time=now,
                    detail={
                        "verdict": result.verdict.value,
                        "score": result.score,
                        "conflict_ratio": result.conflict_ratio,
                    },
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
        # Direct edit (single-actor). For change-controlled profiles, use proposals.
        label = next_version_label(cfg_store, request.profile)
        weights = _weights_from_request(label, request)
        return _apply_config(
            request.profile, weights_to_payload(weights), request.actor, request.note
        )

    @app.post("/v1/config/proposals", response_model=ConfigProposal)
    def propose_config(request: ConfigUpdateRequest) -> ConfigProposal:
        # Validate the weights now (fail fast) so a proposal is always applyable.
        label = next_version_label(cfg_store, request.profile)
        weights = _weights_from_request(label, request)
        return proposal_store.create(
            profile=request.profile,
            payload=weights_to_payload(weights),
            proposed_by=request.actor,
            required_approvals=required_approvals,
            created_time=datetime.now(UTC),
            note=request.note,
        )

    @app.get("/v1/config/proposals", response_model=list[ConfigProposal])
    def list_proposals(status: str | None = None) -> list[ConfigProposal]:
        return proposal_store.list(status=status)

    @app.post("/v1/config/proposals/{proposal_id}/approve", response_model=ConfigProposal)
    def approve_proposal(proposal_id: int, request: ApprovalRequest) -> ConfigProposal:
        try:
            updated = proposal_store.add_approval(proposal_id, request.approver)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="no such proposal") from exc
        except ProposalError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

        if not updated.is_satisfied:
            return updated

        # Threshold met → apply as a new config version, re-stamping the traceable
        # label for the now-current version, and record who approved.
        label = next_version_label(cfg_store, updated.profile)
        payload = {**updated.payload, "version": label}
        record = _apply_config(
            updated.profile,
            payload,
            actor=f"proposal:{proposal_id}",
            note=f"approved by {', '.join(updated.approvals)} (proposed by {updated.proposed_by})",
        )
        return proposal_store.mark_applied(proposal_id, version=record.version)

    @app.get("/v1/audit", response_model=list[AuditRecord])
    def list_audit(
        limit: int = 100, offset: int = 0, target: str | None = None
    ) -> list[AuditRecord]:
        return aud_store.list(limit=limit, offset=offset, target=target)

    @app.post("/v1/audit", response_model=AuditRecord)
    def record_audit(request: AuditCreateRequest) -> AuditRecord:
        # Central audit sink: lets the gateway log admin actions it owns (e.g. API-key
        # management) into the same tamper-evident trail (blueprint §20).
        return aud_store.record(
            actor=request.actor,
            action=request.action,
            target=request.target,
            knowledge_time=datetime.now(UTC),
            before=request.before,
            after=request.after,
        )

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

    # --- Human review queue & appeals (A3) ---

    @app.get("/v1/review", response_model=list[ReviewRecord])
    def list_review(
        status: str | None = None, limit: int = 100, offset: int = 0
    ) -> list[ReviewRecord]:
        return rev_store.list(status=status, limit=limit, offset=offset)

    @app.get("/v1/review/{item_id}", response_model=ReviewRecord)
    def get_review(item_id: int) -> ReviewRecord:
        item = rev_store.get(item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="no such review item")
        return item

    @app.post("/v1/review/{item_id}/resolve", response_model=ReviewRecord)
    def resolve_review(item_id: int, request: ReviewResolveRequest) -> ReviewRecord:
        item = rev_store.get(item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="no such review item")
        if item.status != "open":
            raise HTTPException(status_code=409, detail="review item already resolved")
        if request.decision not in _DECISIONS:
            raise HTTPException(status_code=422, detail=f"decision must be one of {_DECISIONS}")

        resolution: dict[str, object] = {"reviewer": request.reviewer, "decision": request.decision}
        if request.note is not None:
            resolution["note"] = request.note

        if request.decision == "override":
            if request.override_verdict not in _VALID_VERDICTS:
                raise HTTPException(
                    status_code=422, detail="override requires a valid override_verdict"
                )
            if verdict_store is None:
                raise HTTPException(
                    status_code=409, detail="no verdict store configured for overrides"
                )
            now = datetime.now(UTC)
            prior = verdict_store.latest(item.claim_id)
            score_val = (
                request.override_score
                if request.override_score is not None
                else (prior.score if prior is not None else 0.0)
            )
            # INV-OVERRIDE + INV-TEMPORAL: append a NEW, attributed version.
            new_record = verdict_store.append(
                item.claim_id,
                verdict=request.override_verdict,
                score=score_val,
                weights_version="human-override",
                knowledge_time=now,
                event_time=request.event_time,
                payload={
                    "source": "human_override",
                    "reviewer": request.reviewer,
                    "note": request.note,
                    "review_item": item_id,
                    "override_verdict": request.override_verdict,
                },
            )
            resolution["override_verdict"] = request.override_verdict
            resolution["override_score"] = score_val
            resolution["verdict_version"] = new_record.version

        now = datetime.now(UTC)
        resolved = rev_store.resolve(item_id, resolution=resolution, resolved_time=now)
        assert resolved is not None  # we hold the open item above
        aud_store.record(
            actor=request.reviewer,
            action="review.resolve",
            target=f"review:{item_id}",
            knowledge_time=now,
            before=item.model_dump(mode="json"),
            after=resolved.model_dump(mode="json"),
        )
        return resolved

    @app.post("/v1/appeals", response_model=ReviewRecord)
    def submit_appeal(request: AppealRequest) -> ReviewRecord:
        if request.appeal_type not in _APPEAL_TYPES:
            raise HTTPException(
                status_code=422, detail=f"appeal_type must be one of {_APPEAL_TYPES}"
            )
        now = datetime.now(UTC)
        item = rev_store.open_item(
            request.claim_id,
            kind="appeal",
            created_time=now,
            detail={
                "appeal_type": request.appeal_type,
                "body": request.body,
                "submitter": request.submitter,
            },
        )
        # Appeals are logged publicly (blueprint appeals process).
        aud_store.record(
            actor=request.submitter or "public",
            action="appeal.submit",
            target=f"claim:{request.claim_id}",
            knowledge_time=now,
            after=item.model_dump(mode="json"),
        )
        return item

    @app.post("/v1/claim-intake", response_model=ReviewRecord)
    def submit_claim_intake(request: ClaimIntakeRequest) -> ReviewRecord:
        # Public intake: queue a proposed claim for human triage (kind 'claim_intake');
        # a reviewer later promotes it into a real assessment. Logged publicly.
        now = datetime.now(UTC)
        item = rev_store.open_item(
            "intake",
            kind="claim_intake",
            created_time=now,
            detail={"text": request.text, "submitter": request.submitter},
        )
        aud_store.record(
            actor=request.submitter or "public",
            action="claim.intake",
            target=f"review:{item.id}",
            knowledge_time=now,
            after=item.model_dump(mode="json"),
        )
        return item

    @app.get("/v1/appeals", response_model=list[ReviewRecord])
    def list_appeals(limit: int = 100, offset: int = 0) -> list[ReviewRecord]:
        # Appeals are review items of kind 'appeal'; filter the queue.
        appeals = [r for r in rev_store.list(limit=10_000) if r.kind == "appeal"]
        return appeals[offset : offset + limit]

    @app.get("/v1/metrics", response_model=MetricsView)
    def metrics() -> MetricsView:
        snapshot = compute_metrics(verdict_store=verdict_store, review_store=rev_store)
        return MetricsView.model_validate(snapshot)

    @app.get("/v1/calibration/runs", response_model=list[CalibrationRunRecord])
    def list_calibration_runs(limit: int = 100, offset: int = 0) -> list[CalibrationRunRecord]:
        return cal_store.list(limit=limit, offset=offset)

    @app.post("/v1/calibration/runs", response_model=CalibrationRunRecord)
    def record_calibration_run() -> CalibrationRunRecord:
        # Re-run the gold benchmark now and append the result to the ledger (§28.12),
        # so accuracy/calibration trends are tracked and regressions are visible.
        bench = benchmark_metrics()
        if bench is None:
            raise HTTPException(status_code=503, detail="benchmark seed unavailable")
        return cal_store.record(
            recorded_time=datetime.now(UTC),
            total=bench["total"],
            verdict_accuracy=bench["verdict_accuracy"],
            calibration_error=bench["calibration_error"],
            payload={"by_difficulty": bench["by_difficulty"]},
        )

    return app


app = create_app()
