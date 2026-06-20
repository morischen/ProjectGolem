"""Claim Engine — normalizes raw input into Claim objects.

The LLM extracts and classifies (via a recorded wrapper, ADR-0005); it never
scores or assigns verdicts (INV-DETERMINISM). Scoring is the Trust Engine's job.
"""

from eip_claim._generated.claim import Claim, ClaimType
from eip_claim.extractor import ExtractionResult, build_prompt, extract_claim
from eip_claim.llm import AnthropicLLMClient, LLMClient, RecordedCall, StubLLMClient

__all__ = [
    "Claim",
    "ClaimType",
    "ExtractionResult",
    "build_prompt",
    "extract_claim",
    "AnthropicLLMClient",
    "LLMClient",
    "RecordedCall",
    "StubLLMClient",
]
