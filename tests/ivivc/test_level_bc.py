"""Tests for IVIVC Level B / Level C helpers (MDT, MRT, correlations).

References
----------
FDA Guidance for Industry: Extended Release Oral Dosage Forms: Development,
Evaluation, and Application of In Vitro/In Vivo Correlations (1997). CDER.

Gibaldi, M., & Perrier, D. (1982). Pharmacokinetics (2nd ed.). Marcel Dekker.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from openpkflow.ivivc import (
    LinearCorrelationResult,
    level_b_correlation,
    level_c_correlation,
    mean_dissolution_time,
    mean_residence_time,
)


class TestMeanDissolutionTime:
    """Tests for mean_dissolution_time."""

    def test_two_point_hand_check(self) -> None:
        """Degenerate two-point MDT is the interval midpoint.

        If Q goes from 0 at t=0 to 1 at t=2, all mass dissolves in [0, 2]
        with midpoint t_mid=1, so MDT = 1.

        Reference: first-moment definition MDT = sum(t_mid * dQ) / Q_last;
        FDA ER IVIVC guidance (1997) Level B uses MDT as the in vitro moment.
        """
        mdt = mean_dissolution_time([0.0, 2.0], [0.0, 1.0])
        assert math.isclose(mdt, 1.0, rel_tol=1e-12)

    def test_zero_order_dissolution_mdt_half_time(self) -> None:
        """Zero-order complete release by T has MDT = T/2.

        Reference
        ---------
        For constant dissolution rate, MDT = T/2 where T is the time to
        complete release (first statistical moment of a rectangular rate).
        See also FDA ER IVIVC guidance (1997) discussion of mean dissolution
        time as the in vitro moment for Level B correlations.
        """
        # Linear cumulative fraction from 0 to 1 over 0..10 h
        t = np.linspace(0.0, 10.0, 21)
        q = t / 10.0
        mdt = mean_dissolution_time(t, q)
        assert math.isclose(mdt, 5.0, rel_tol=1e-6, abs_tol=1e-6)

    def test_percent_scale_cancels(self) -> None:
        t = [0.0, 1.0, 2.0, 4.0]
        frac = [0.0, 0.25, 0.60, 1.0]
        pct = [0.0, 25.0, 60.0, 100.0]
        assert math.isclose(
            mean_dissolution_time(t, frac),
            mean_dissolution_time(t, pct),
            rel_tol=1e-12,
        )

    def test_zero_final_raises(self) -> None:
        with pytest.raises(ValueError, match="Final fraction"):
            mean_dissolution_time([0.0, 1.0], [0.0, 0.0])

    def test_decreasing_raises(self) -> None:
        with pytest.raises(ValueError, match="non-decreasing"):
            mean_dissolution_time([0.0, 1.0, 2.0], [0.0, 0.5, 0.2])


class TestMeanResidenceTime:
    """Tests for mean_residence_time."""

    def test_iv_bolus_monoexponential_truncated(self) -> None:
        """MRT for monoexponential C(t)=C0*exp(-k t) approaches 1/k.

        Degenerate/sanity: with dense sampling to late times, truncated
        AUMC/AUC approaches 1/k.

        Reference: Gibaldi & Perrier (1982), MRT = 1/k for IV bolus
        one-compartment (AUMC/AUC = 1/k).
        """
        k = 0.2
        c0 = 10.0
        t = np.linspace(0.0, 40.0, 401)  # 8 half-lives
        c = c0 * np.exp(-k * t)
        mrt = mean_residence_time(t, c)
        # Truncation leaves a small positive bias relative to true 1/k
        assert math.isclose(mrt, 1.0 / k, rel_tol=0.05)

    def test_hand_check_two_point(self) -> None:
        """Two-point AUMC/AUC hand calculation.

        t=[0, 2], C=[2, 0]: AUC = 2, AUMC = integral t*C.
        Trapezoid on t*C: points (0,0) and (2,0) -> AUMC=0? Wait C at 0 is 2,
        t*C = [0, 0], AUMC=0, MRT=0 -- edge case.

        Use t=[0,1,2], C=[4,2,0]:
        AUC = 0.5*(4+2)*1 + 0.5*(2+0)*1 = 3+1 = 4
        tC = [0, 2, 0]
        AUMC = 0.5*(0+2)*1 + 0.5*(2+0)*1 = 1+1 = 2
        MRT = 2/4 = 0.5

        Reference: Gibaldi & Perrier (1982) definition MRT = AUMC/AUC.
        """
        mrt = mean_residence_time([0.0, 1.0, 2.0], [4.0, 2.0, 0.0])
        assert math.isclose(mrt, 0.5, rel_tol=1e-12)

    def test_negative_conc_raises(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            mean_residence_time([0.0, 1.0], [1.0, -0.1])


class TestLevelBCorrelation:
    """Tests for level_b_correlation (MDT vs MRT)."""

    def test_perfect_identity_line(self) -> None:
        """Degenerate: MDT == MRT for all points gives slope=1, R^2=1.

        Reference: FDA ER IVIVC (1997) Level B is a linear correlation of
        MDT with MRT; perfect 1:1 correspondence is the ideal case.
        """
        vals = [1.0, 2.0, 3.0, 4.0]
        res = level_b_correlation(vals, vals)
        assert isinstance(res, LinearCorrelationResult)
        assert math.isclose(res.slope, 1.0, abs_tol=1e-12)
        assert math.isclose(res.intercept, 0.0, abs_tol=1e-12)
        assert math.isclose(res.r, 1.0, abs_tol=1e-12)
        assert math.isclose(res.r_squared, 1.0, abs_tol=1e-12)
        assert res.n == 4

    def test_known_linear_relationship(self) -> None:
        """Known OLS fit: MRT = 2*MDT + 1.

        Reference: FDA ER IVIVC guidance (1997), Level B linear correlation
        methodology (ordinary least squares of in vivo moment on in vitro).
        """
        mdt = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        mrt = 2.0 * mdt + 1.0
        res = level_b_correlation(mdt, mrt)
        assert math.isclose(res.slope, 2.0, abs_tol=1e-12)
        assert math.isclose(res.intercept, 1.0, abs_tol=1e-12)
        assert math.isclose(res.r_squared, 1.0, abs_tol=1e-12)

    def test_length_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            level_b_correlation([1.0, 2.0], [1.0])


class TestLevelCCorrelation:
    """Tests for level_c_correlation (single metrics)."""

    def test_degenerate_constant_pk_metric(self) -> None:
        """If PK metric is constant, OLS slope is ~0 and intercept is the constant.

        Reference: FDA ER IVIVC (1997) Level C correlates a dissolution
        metric with a PK metric; degenerate constant response yields a flat
        regression (slope ~ 0).
        """
        x = [10.0, 20.0, 30.0, 40.0]
        y = [5.0, 5.0, 5.0, 5.0]
        res = level_c_correlation(x, y)
        assert math.isclose(res.slope, 0.0, abs_tol=1e-12)
        assert math.isclose(res.intercept, 5.0, abs_tol=1e-12)
        assert res.n == 4

    def test_percent_dissolved_vs_cmax_linear(self) -> None:
        """Level C example: %dissolved at 30 min vs Cmax linear fit.

        Reference
        ---------
        FDA Guidance for Industry: Extended Release Oral Dosage Forms (1997),
        Level C correlations (single-point dissolution metric vs PK metric).
        """
        pct_30 = [40.0, 55.0, 70.0, 85.0]
        cmax = [8.0, 11.0, 14.0, 17.0]  # slope 0.2, intercept 0
        res = level_c_correlation(pct_30, cmax)
        assert math.isclose(res.slope, 0.2, abs_tol=1e-10)
        assert math.isclose(res.intercept, 0.0, abs_tol=1e-10)
        assert math.isclose(res.r, 1.0, abs_tol=1e-12)
