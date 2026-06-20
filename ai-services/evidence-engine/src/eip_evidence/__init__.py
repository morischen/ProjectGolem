"""Evidence Retrieval Engine — retrieves and classifies candidate evidence.

The LLM assigns each candidate's relation to the claim (via a recorded wrapper,
ADR-0005); it never scores. Output `Evidence` feeds the deterministic Trust Engine.
"""

from eip_llm import AnthropicLLMClient, LLMClient, RecordedCall, StubLLMClient

from eip_evidence._generated.evidence import Evidence, EvidenceRelation
from eip_evidence.engine import GatherResult, build_prompt, classify_candidate, gather
from eip_evidence.models import Candidate
from eip_evidence.retriever import Retriever, StubRetriever

__all__ = [
    "Evidence",
    "EvidenceRelation",
    "Candidate",
    "GatherResult",
    "build_prompt",
    "classify_candidate",
    "gather",
    "Retriever",
    "StubRetriever",
    "AnthropicLLMClient",
    "LLMClient",
    "RecordedCall",
    "StubLLMClient",
]
