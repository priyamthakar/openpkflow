"""lambda_z auto-selection adjusted R-squared tolerance vs. PKNCA.

PKNCA ``pk.calc.half.life()`` (documented rule, log-linear method) keeps the
windows whose adjusted R-squared is within ``adj.r.squared.factor`` (default
1e-4) of the best and then selects the one with the most points. Reference
values were produced by ``scripts/pknca_lambda_z_tolerance_crossval.R`` with
PKNCA 0.12.1.9002 (GitHub commit 9e0a391) on R 4.5.3.

Source: PKNCA R package, https://github.com/humanpred/pknca,
``pk.calc.half.life()`` documentation.
"""

from __future__ import annotations

import pytest

from openpkflow.nca.methods import lambda_z

_TIMES = [0.0, 0.5, 1.0, 2.0, 4.0, 6.0, 8.0, 12.0, 16.0, 24.0]
_NEAR = [0.0, 4.654, 6.191, 6.865, 5.359, 4.163, 3.017, 1.634, 0.879, 0.27]
_FAR = [0.0, 4.706, 6.461, 6.559, 5.665, 4.138, 2.948, 1.692, 0.921, 0.276]

# (profile, tolerance) -> (lambda_z, adj_r2, n_points, half_life) from PKNCA.
_PKNCA_REFERENCE = {
    ("near", 1e-4): (0.151866310953291, 0.999733655945934, 5, 4.56419317891468),
    ("near", 1e-12): (0.150827885512162, 0.999780276576844, 4, 4.59561690602665),
    ("far", 1e-4): (0.151037890505968, 0.999989188489916, 3, 4.58922710213935),
    ("far", 1e-12): (0.151037890505968, 0.999989188489916, 3, 4.58922710213935),
}
_PROFILES = {"near": _NEAR, "far": _FAR}


@pytest.mark.parametrize(("profile", "tolerance"), sorted(_PKNCA_REFERENCE))
def test_lambda_z_matches_pknca_adj_r2_factor(profile: str, tolerance: float) -> None:
    expected_lz, expected_adj_r2, expected_n, expected_hl = _PKNCA_REFERENCE[(profile, tolerance)]

    result = lambda_z(_TIMES, _PROFILES[profile], adj_r2_tolerance=tolerance)

    assert result.n_points == expected_n
    assert result.lambda_z == pytest.approx(expected_lz, rel=1e-10)
    assert result.adj_r_squared == pytest.approx(expected_adj_r2, rel=1e-10)
    assert result.half_life == pytest.approx(expected_hl, rel=1e-10)


def test_default_tolerance_is_pknca_default() -> None:
    """Default selection equals PKNCA's default adj.r.squared.factor = 1e-4."""
    assert lambda_z(_TIMES, _NEAR).n_points == 5


def test_zero_tolerance_requires_exact_tie() -> None:
    """With no tolerance the best adjusted R-squared window (4 points) wins."""
    assert lambda_z(_TIMES, _NEAR, adj_r2_tolerance=0.0).n_points == 4


@pytest.mark.parametrize("bad", [-1e-4, float("nan"), float("inf")])
def test_invalid_tolerance_raises(bad: float) -> None:
    with pytest.raises(ValueError, match="adj_r2_tolerance"):
        lambda_z(_TIMES, _NEAR, adj_r2_tolerance=bad)


def test_include_tmax_allows_cmax_in_terminal_window() -> None:
    """IV bolus: the first sample is Cmax and lies on the log-linear decline.

    Expected value is the simulating rate constant (C = 10 exp(-0.3 t),
    Gibaldi & Perrier 1982 Eq. 1-2). PKNCA's default excludes the Tmax sample
    (``allow.tmax.in.half.life = FALSE``); Phoenix WinNonlin includes it for
    IV bolus.
    """
    import math

    times = [0.25, 0.5, 1.0, 2.0]
    concs = [10.0 * math.exp(-0.3 * t) for t in times]

    default = lambda_z(times, concs)
    with_tmax = lambda_z(times, concs, include_tmax=True)

    assert default.n_points == 3
    assert with_tmax.n_points == 4
    assert with_tmax.time_start == 0.25
    assert with_tmax.lambda_z == pytest.approx(0.3, rel=1e-12)
