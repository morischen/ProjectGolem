"""Tests for the offline embedders (ADR-0006/0011)."""

import math

from eip_evidence import Embedder, HashingEmbedder, StubEmbedder


def _cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def test_satisfies_protocol():
    assert isinstance(HashingEmbedder(), Embedder)
    assert isinstance(StubEmbedder(), Embedder)


def test_deterministic_and_normalized():
    emb = HashingEmbedder(dim=64)
    v1 = emb.embed("the quick brown fox")
    v2 = emb.embed("the quick brown fox")
    assert v1 == v2  # reproducible (INV-REPRO)
    assert math.isclose(_cosine(v1, v1), 1.0, abs_tol=1e-9)  # unit length


def test_shared_vocabulary_is_more_similar():
    emb = HashingEmbedder(dim=512)
    base = emb.embed("ceasefire violation reported near the northern border")
    near = emb.embed("a ceasefire violation was reported at the northern border")
    far = emb.embed("quarterly economic growth exceeded analyst expectations")
    assert _cosine(base, near) > _cosine(base, far)


def test_empty_text_is_safe():
    v = HashingEmbedder(dim=16).embed("")
    assert len(v) == 16
    assert all(x == 0.0 for x in v)


def test_dim_is_respected():
    assert len(HashingEmbedder(dim=128).embed("hello world")) == 128
