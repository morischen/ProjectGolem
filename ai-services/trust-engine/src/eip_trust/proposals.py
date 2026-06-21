"""Multi-approver change control for scoring config (governance, blueprint §20).

A high-leverage methodology change (scoring weights/thresholds/tier reliability)
shouldn't be a single click. A `ConfigProposal` captures a *pending* change and the
approvals it has collected; it only becomes an applied config version once enough
**distinct** approvers — none of them the proposer (separation of duties) — sign off.
This module owns the proposal state machine; applying an approved proposal (writing
the new config version + audit entry) stays in the API layer next to the stores.
In-memory like the other default stores; SQL-backing is a follow-up.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ConfigProposal(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int = Field(ge=1)
    profile: str
    payload: dict[str, Any] = Field(description="Proposed config document (weights).")
    proposed_by: str
    note: str | None = None
    required_approvals: int = Field(ge=1)
    approvals: list[str] = Field(default_factory=list)
    status: str = Field(default="pending", description="'pending' | 'approved'.")
    created_time: datetime
    applied_version: int | None = None

    @property
    def is_satisfied(self) -> bool:
        return len(self.approvals) >= self.required_approvals


class ProposalError(ValueError):
    """A governance-rule violation (duplicate/self approval, already applied)."""


class InMemoryProposalStore:
    def __init__(self) -> None:
        self._items: dict[int, ConfigProposal] = {}
        self._seq = 0

    def create(
        self,
        *,
        profile: str,
        payload: dict[str, Any],
        proposed_by: str,
        required_approvals: int,
        created_time: datetime,
        note: str | None = None,
    ) -> ConfigProposal:
        self._seq += 1
        proposal = ConfigProposal(
            id=self._seq,
            profile=profile,
            payload=dict(payload),
            proposed_by=proposed_by,
            note=note,
            required_approvals=required_approvals,
            created_time=created_time,
        )
        self._items[proposal.id] = proposal
        return proposal

    def get(self, proposal_id: int) -> ConfigProposal | None:
        return self._items.get(proposal_id)

    def list(self, *, status: str | None = None) -> list[ConfigProposal]:
        rows = [p for p in self._items.values() if status is None or p.status == status]
        return sorted(rows, key=lambda p: p.id, reverse=True)

    def add_approval(self, proposal_id: int, approver: str) -> ConfigProposal:
        """Record a distinct approver's sign-off. Raises ProposalError on a governance
        violation. Does not apply the change — the caller checks `is_satisfied`."""
        proposal = self._items.get(proposal_id)
        if proposal is None:
            raise KeyError(proposal_id)
        if proposal.status != "pending":
            raise ProposalError("proposal is not pending")
        if approver == proposal.proposed_by:
            raise ProposalError("the proposer cannot approve their own change")
        if approver in proposal.approvals:
            raise ProposalError("this approver already signed off")
        updated = proposal.model_copy(update={"approvals": [*proposal.approvals, approver]})
        self._items[proposal_id] = updated
        return updated

    def mark_applied(self, proposal_id: int, *, version: int) -> ConfigProposal:
        proposal = self._items[proposal_id]
        applied = proposal.model_copy(update={"status": "approved", "applied_version": version})
        self._items[proposal_id] = applied
        return applied
