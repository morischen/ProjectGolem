"""Internal models for the Evidence Retrieval Engine.

`Candidate` is a retrieved source before classification. After the LLM assigns a
relation, the engine emits an `Evidence` (the cross-service contract) — quality,
freshness, and source_tier come from retrieval metadata, not the LLM.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Candidate(BaseModel):
    """A retrieved candidate source, pre-classification."""

    model_config = ConfigDict(extra="forbid")

    id: str
    source_id: str = Field(description="Stable id of the originating source.")
    source_tier: int = Field(ge=1, le=4, description="1=primary … 4=emerging.")
    content: str = Field(description="The retrieved text to classify against the claim.")
    quality: float = Field(default=0.5, ge=0.0, le=1.0)
    freshness: float = Field(default=0.5, ge=0.0, le=1.0)
