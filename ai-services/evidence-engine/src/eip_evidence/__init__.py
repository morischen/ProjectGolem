"""Evidence Retrieval Engine — retrieves and classifies candidate evidence.

The LLM assigns each candidate's relation to the claim (via a recorded wrapper,
ADR-0005); it never scores. Output `Evidence` feeds the deterministic Trust Engine.
"""

from eip_llm import AnthropicLLMClient, LLMClient, RecordedCall, StubLLMClient

from eip_evidence._generated.evidence import Evidence, EvidenceRelation
from eip_evidence.embedding import Embedder, StubEmbedder
from eip_evidence.engine import GatherResult, build_prompt, classify_candidate, gather
from eip_evidence.graph_retriever import GraphRetriever
from eip_evidence.graphstore import GraphHit, GraphStore, Neo4jGraphStore, make_neo4j_store
from eip_evidence.independence import IndependenceReport, assess_independence
from eip_evidence.models import Candidate
from eip_evidence.retriever import Retriever, StubRetriever
from eip_evidence.semantic_retriever import SemanticRetriever
from eip_evidence.vectorstore import (
    QdrantVectorStore,
    VectorHit,
    VectorStore,
    make_qdrant_store,
)

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
    "SemanticRetriever",
    "Embedder",
    "StubEmbedder",
    "VectorStore",
    "VectorHit",
    "QdrantVectorStore",
    "make_qdrant_store",
    "GraphRetriever",
    "GraphStore",
    "GraphHit",
    "Neo4jGraphStore",
    "make_neo4j_store",
    "IndependenceReport",
    "assess_independence",
    "AnthropicLLMClient",
    "LLMClient",
    "RecordedCall",
    "StubLLMClient",
]
