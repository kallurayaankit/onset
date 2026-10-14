
"""Tests for the stats module. No git, no network."""

from onset.stats import two_proportion_p_value


def test_identical_rates_give_high_p():
    # 5/10 vs 5/10 -> no difference -> p should be 1.0
    p = two_proportion_p_value(5, 10, 5, 10)
    assert p == 1.0


def test_very_different_rates_give_low_p():
    # 0/20 vs 15/20 -> hugely different -> small p
    p = two_proportion_p_value(0, 20, 15, 20)
    assert p < 0.01


def test_extreme_both_zero():
    # Both 0 failures -> no signal, p = 1.0
    assert two_proportion_p_value(0, 10, 0, 10) == 1.0


def test_extreme_both_full():
    # Both 10 failures -> no signal, p = 1.0
    assert two_proportion_p_value(10, 10, 10, 10) == 1.0


def test_zero_runs_returns_one():
    assert two_proportion_p_value(0, 0, 5, 10) == 1.0


def test_mild_difference_not_significant():
    # 2/20 vs 4/20 -> p should be > 0.05
    p = two_proportion_p_value(2, 20, 4, 20)
    assert p > 0.05


def test_p_in_range():
    for a, b, c, d in [(0, 10, 5, 10), (1, 10, 9, 10), (3, 20, 3, 20)]:
        p = two_proportion_p_value(a, b, c, d)
        assert 0.0 <= p <= 1.0
