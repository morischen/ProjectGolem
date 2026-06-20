"""Tests for the freshness-from-age helper."""

import pytest

from eip_trust import freshness_from_age_days


def test_age_zero_is_full_freshness():
    assert freshness_from_age_days(0) == 1.0


def test_half_life_halves():
    assert freshness_from_age_days(365, 365) == pytest.approx(0.5)
    assert freshness_from_age_days(730, 365) == pytest.approx(0.25)


def test_monotonic_decreasing():
    a = freshness_from_age_days(10)
    b = freshness_from_age_days(100)
    c = freshness_from_age_days(1000)
    assert a > b > c
    assert all(0.0 < v <= 1.0 for v in (a, b, c))


def test_large_half_life_decays_slowly():
    # Historical domain: a 5-year-old source is still quite fresh with a 20y half-life.
    assert freshness_from_age_days(365 * 5, 365 * 20) > 0.8


def test_invalid_inputs_rejected():
    with pytest.raises(ValueError):
        freshness_from_age_days(-1)
    with pytest.raises(ValueError):
        freshness_from_age_days(10, 0)
