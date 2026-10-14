
"""Statistical helpers. No dependencies beyond stdlib."""

from math import erf, sqrt


def norm_cdf(x):
    """Standard normal CDF."""
    return 0.5 * (1.0 + erf(x / sqrt(2.0)))


def two_proportion_p_value(f1, n1, f2, n2):
    """Two-tailed p-value for the difference between two proportions.

    f1, f2 = failure counts. n1, n2 = total runs.
    Uses a pooled two-proportion z-test. Returns a p-value in [0, 1].

    Interpretation: if p is small, the two proportions are different.
    We use this as the "is the flake rate genuinely different at the
    two commits" test.
    """
    if n1 == 0 or n2 == 0:
        return 1.0

    p1 = f1 / n1
    p2 = f2 / n2
    p_pool = (f1 + f2) / (n1 + n2)

    if p_pool == 0.0 or p_pool == 1.0:
        # Both samples have the same extreme rate; treat as indistinguishable
        return 1.0

    se = sqrt(p_pool * (1.0 - p_pool) * (1.0 / n1 + 1.0 / n2))
    if se == 0.0:
        return 1.0

    z = abs(p1 - p2) / se
    p = 2.0 * (1.0 - norm_cdf(z))
    return max(0.0, min(1.0, p))
