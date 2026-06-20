"""Tests for independence / citation-laundering analysis."""

import pytest

from eip_evidence import assess_independence


def test_independent_sources_score_one():
    report = assess_independence(["a", "b", "c"], [])
    assert report.distinct_sources == 3
    assert report.independent_groups == 3
    assert report.independence_ratio == 1.0
    assert report.groups == [["a"], ["b"], ["c"]]


def test_shared_origin_collapses_to_one_group():
    # b, c, d all cite the same origin a -> one independent voice, not three.
    report = assess_independence(["b", "c", "d"], [("b", "a"), ("c", "a"), ("d", "a")])
    assert report.independent_groups == 1
    assert report.independence_ratio == pytest.approx(1 / 3)
    assert report.groups == [["a", "b", "c", "d"]]


def test_citation_cycle_is_one_group():
    report = assess_independence(["a", "b"], [("a", "b"), ("b", "a")])
    assert report.independent_groups == 1
    assert report.independence_ratio == 0.5


def test_mixed_independent_and_laundered():
    # a<-b are one cluster; c and d independent -> 3 groups across 4 sources.
    report = assess_independence(["a", "b", "c", "d"], [("b", "a")])
    assert report.independent_groups == 3
    assert report.independence_ratio == 0.75
    assert ["a", "b"] in report.groups


def test_empty_is_fully_independent():
    report = assess_independence([], [])
    assert report.distinct_sources == 0
    assert report.independent_groups == 0
    assert report.independence_ratio == 1.0
    assert report.groups == []
