"""Tests for sim/methods.py: pure analytical PK equations.

Each function is tested with:
1. A degenerate/sanity case with a hand-checkable answer.
2. A published reference case with source citation in the docstring.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from openpkflow.sim.methods import (
    c_1cmt_iv_bolus,
    c_1cmt_iv_infusion,
    c_1cmt_oral,
    c_2cmt_iv_bolus,
    c_2cmt_iv_infusion,
    c_2cmt_oral,
    superpose,
)

# ---------------------------------------------------------------------------
# 1-compartment IV bolus
# ---------------------------------------------------------------------------


class TestC1CmtIVBolus:
    """Tests for c_1cmt_iv_bolus."""

    def test_at_t0_equals_dose_over_vz(self) -> None:
        """At t=0, C = D/Vz (degenerate sanity).

        Reference: Gibaldi & Perrier 2nd ed. (1982), Eq. 1-2.
        """
        C = c_1cmt_iv_bolus([0.0], dose=100.0, CL=5.0, Vz=20.0)
        assert math.isclose(C[0], 100.0 / 20.0, rel_tol=1e-10)

    def test_mono_exponential_decay(self) -> None:
        """C(t) = (D/Vz)*exp(-k*t) with k=CL/Vz.

        Reference: Gibaldi & Perrier 2nd ed. (1982), Eq. 1-2.
        """
        CL, Vz, dose = 10.0, 50.0, 500.0
        k = CL / Vz
        t = np.linspace(0, 24, 100)
        C = c_1cmt_iv_bolus(t, dose=dose, CL=CL, Vz=Vz)
        expected = (dose / Vz) * np.exp(-k * t)
        np.testing.assert_allclose(C, expected, rtol=1e-12)

    def test_half_life_halving(self) -> None:
        """Concentration halves at t = t_half.

        Reference: by definition of half-life.
        """
        CL, Vz, dose = 2.0, 10.0, 100.0
        t_half = math.log(2) / (CL / Vz)
        C0 = c_1cmt_iv_bolus([0.0], dose=dose, CL=CL, Vz=Vz)[0]
        C_half = c_1cmt_iv_bolus([t_half], dose=dose, CL=CL, Vz=Vz)[0]
        assert math.isclose(C_half, C0 / 2.0, rel_tol=1e-10)

    def test_raises_on_invalid_params(self) -> None:
        with pytest.raises(ValueError, match="CL must be > 0"):
            c_1cmt_iv_bolus([1.0], dose=100.0, CL=0.0, Vz=10.0)
        with pytest.raises(ValueError, match="Vz must be > 0"):
            c_1cmt_iv_bolus([1.0], dose=100.0, CL=5.0, Vz=-1.0)
        with pytest.raises(ValueError, match="dose must be >= 0"):
            c_1cmt_iv_bolus([1.0], dose=-10.0, CL=5.0, Vz=10.0)

    def test_raises_on_invalid_times(self) -> None:
        with pytest.raises(ValueError, match="strictly increasing"):
            c_1cmt_iv_bolus([2.0, 1.0], dose=100.0, CL=5.0, Vz=10.0)
        with pytest.raises(ValueError, match="non-empty"):
            c_1cmt_iv_bolus([], dose=100.0, CL=5.0, Vz=10.0)


# ---------------------------------------------------------------------------
# 1-compartment IV infusion
# ---------------------------------------------------------------------------


class TestC1CmtIVInfusion:
    """Tests for c_1cmt_iv_infusion."""

    def test_at_t0_is_zero(self) -> None:
        """C(0) = 0 for a constant-rate infusion.

        Reference: Gibaldi & Perrier 2nd ed. (1982), Eq. 2-1.
        """
        C = c_1cmt_iv_infusion([0.0], dose=100.0, CL=5.0, Vz=20.0, t_inf=2.0)
        assert math.isclose(C[0], 0.0, abs_tol=1e-12)

    def test_during_infusion_formula(self) -> None:
        """During infusion: C(t) = (R0/CL)*(1 - exp(-k*t)).

        Reference: Gibaldi & Perrier 2nd ed. (1982), Eq. 2-1.
        """
        CL, Vz, dose, t_inf = 5.0, 20.0, 100.0, 2.0
        k = CL / Vz
        R0 = dose / t_inf
        t_mid = 1.0
        C = c_1cmt_iv_infusion([t_mid], dose=dose, CL=CL, Vz=Vz, t_inf=t_inf)
        expected = (R0 / CL) * (1.0 - math.exp(-k * t_mid))
        assert math.isclose(C[0], expected, rel_tol=1e-10)

    def test_after_infusion_formula(self) -> None:
        """After infusion: C(t) = C_peak * exp(-k*(t - t_inf)).

        Reference: Gibaldi & Perrier 2nd ed. (1982), Eq. 2-1.
        """
        CL, Vz, dose, t_inf = 5.0, 20.0, 100.0, 2.0
        k = CL / Vz
        R0 = dose / t_inf
        C_peak = (R0 / CL) * (1.0 - math.exp(-k * t_inf))
        t_post = 4.0
        C = c_1cmt_iv_infusion([t_post], dose=dose, CL=CL, Vz=Vz, t_inf=t_inf)
        expected = C_peak * math.exp(-k * (t_post - t_inf))
        assert math.isclose(C[0], expected, rel_tol=1e-10)

    def test_continuity_at_t_inf(self) -> None:
        """Profile must be continuous at the end of the infusion."""
        CL, Vz, dose, t_inf = 3.0, 15.0, 75.0, 1.0
        eps = 1e-8
        C_before = c_1cmt_iv_infusion([t_inf - eps], dose=dose, CL=CL, Vz=Vz, t_inf=t_inf)
        C_after = c_1cmt_iv_infusion([t_inf + eps], dose=dose, CL=CL, Vz=Vz, t_inf=t_inf)
        assert math.isclose(C_before[0], C_after[0], rel_tol=1e-4)

    def test_raises_on_invalid_t_inf(self) -> None:
        with pytest.raises(ValueError, match="t_inf must be > 0"):
            c_1cmt_iv_infusion([1.0], dose=100.0, CL=5.0, Vz=10.0, t_inf=0.0)


# ---------------------------------------------------------------------------
# 1-compartment oral
# ---------------------------------------------------------------------------


class TestC1CmtOral:
    """Tests for c_1cmt_oral."""

    def test_at_t0_is_zero(self) -> None:
        """C(0) = 0 for oral dosing (absorption hasn't started).

        Reference: Gibaldi & Perrier 2nd ed. (1982), Eq. 1-13 (Bateman).
        """
        C = c_1cmt_oral([0.0], dose=100.0, CL_F=5.0, Vz_F=20.0, ka=1.5)
        assert math.isclose(C[0], 0.0, abs_tol=1e-12)

    def test_bateman_equation(self) -> None:
        """C(t) = D*ka/(Vz_F*(ka-k)) * (exp(-k*t) - exp(-ka*t)).

        Reference: Gibaldi & Perrier 2nd ed. (1982), Eq. 1-13.
        """
        CL_F, Vz_F, ka, dose = 5.0, 20.0, 1.5, 100.0
        k = CL_F / Vz_F
        t_vec = np.array([0.0, 0.5, 1.0, 2.0, 4.0, 8.0])
        C = c_1cmt_oral(t_vec, dose=dose, CL_F=CL_F, Vz_F=Vz_F, ka=ka)
        expected = (dose * ka / (Vz_F * (ka - k))) * (np.exp(-k * t_vec) - np.exp(-ka * t_vec))
        np.testing.assert_allclose(C, expected, rtol=1e-12)

    def test_flip_flop_case(self) -> None:
        """When ka == k, use L'Hopital limit: C(t) = (D*k/Vz_F)*t*exp(-k*t).

        Reference: L'Hopital's rule applied to Eq. 1-13 as ka -> k.
        """
        CL_F, Vz_F, dose = 5.0, 20.0, 100.0
        k = CL_F / Vz_F
        ka = k  # exact equality
        t_vec = np.array([0.0, 0.5, 1.0, 2.0, 4.0])
        C = c_1cmt_oral(t_vec, dose=dose, CL_F=CL_F, Vz_F=Vz_F, ka=ka)
        expected = (dose * k / Vz_F) * t_vec * np.exp(-k * t_vec)
        np.testing.assert_allclose(C, expected, rtol=1e-12)

    def test_positive_concentrations(self) -> None:
        """All concentrations must be >= 0."""
        t = np.linspace(0, 48, 200)
        C = c_1cmt_oral(t, dose=100.0, CL_F=3.0, Vz_F=30.0, ka=0.8)
        assert np.all(C >= 0.0)


# ---------------------------------------------------------------------------
# 2-compartment IV bolus
# ---------------------------------------------------------------------------


class TestC2CmtIVBolus:
    """Tests for c_2cmt_iv_bolus."""

    def test_at_t0_equals_dose_over_v1(self) -> None:
        """At t=0, C = D/V1 (sum of bi-exponential coefficients = D/V1).

        Reference: Gibaldi & Perrier 2nd ed. (1982), Eq. 3-1.
        """
        CL, V1, Q, V2, dose = 5.0, 20.0, 3.0, 15.0, 100.0
        C = c_2cmt_iv_bolus([0.0], dose=dose, CL=CL, V1=V1, Q=Q, V2=V2)
        assert math.isclose(C[0], dose / V1, rel_tol=1e-10)

    def test_biexponential_shape(self) -> None:
        """Profile must equal A*exp(-alpha*t) + B*exp(-beta*t) with A+B = D/V1.

        Reference: Gibaldi & Perrier 2nd ed. (1982), Eq. 3-1 and 3-2.
        """
        CL, V1, Q, V2, dose = 5.0, 20.0, 3.0, 15.0, 100.0
        k10 = CL / V1
        k12 = Q / V1
        k21 = Q / V2
        s1 = k10 + k12 + k21
        disc = math.sqrt(s1 * s1 - 4 * k10 * k21)
        alpha = (s1 + disc) / 2.0
        beta = (s1 - disc) / 2.0
        A = (dose / V1) * (alpha - k21) / (alpha - beta)
        B = (dose / V1) * (k21 - beta) / (alpha - beta)

        t = np.linspace(0, 24, 50)
        C = c_2cmt_iv_bolus(t, dose=dose, CL=CL, V1=V1, Q=Q, V2=V2)
        expected = A * np.exp(-alpha * t) + B * np.exp(-beta * t)
        np.testing.assert_allclose(C, expected, rtol=1e-12)

    def test_coefficients_sum_to_d_over_v1(self) -> None:
        """A + B = D/V1 (initial condition check).

        Reference: Gibaldi & Perrier 2nd ed. (1982), p. 62.
        """
        CL, V1, Q, V2, dose = 8.0, 30.0, 4.0, 20.0, 200.0
        C0 = c_2cmt_iv_bolus([0.0], dose=dose, CL=CL, V1=V1, Q=Q, V2=V2)
        assert math.isclose(C0[0], dose / V1, rel_tol=1e-10)

    def test_collapses_to_1cmt_when_q_near_zero(self) -> None:
        """With very small Q, 2-cmt IV bolus approaches 1-cmt IV bolus.

        Reference: limiting behaviour as Q -> 0.
        """
        CL, V1, Q, V2, dose = 5.0, 20.0, 1e-8, 1.0, 100.0
        t = np.linspace(0.1, 24, 50)
        C2 = c_2cmt_iv_bolus(t, dose=dose, CL=CL, V1=V1, Q=Q, V2=V2)
        C1 = c_1cmt_iv_bolus(t, dose=dose, CL=CL, Vz=V1)
        np.testing.assert_allclose(C2, C1, rtol=1e-4)


# ---------------------------------------------------------------------------
# 2-compartment IV infusion
# ---------------------------------------------------------------------------


class TestC2CmtIVInfusion:
    """Tests for c_2cmt_iv_infusion."""

    def test_at_t0_is_zero(self) -> None:
        """C(0) = 0 for constant-rate infusion (no drug yet delivered).

        Reference: Gibaldi & Perrier 2nd ed. (1982), Eqs. 3-28 to 3-30, p. 75.
        """
        C = c_2cmt_iv_infusion([0.0], dose=100.0, CL=5.0, V1=20.0, Q=3.0, V2=15.0, t_inf=2.0)
        assert math.isclose(C[0], 0.0, abs_tol=1e-12)

    def test_during_infusion_formula(self) -> None:
        """During infusion: matches biexponential ramp formula.

        Reference: Gibaldi & Perrier 2nd ed. (1982), Eqs. 3-28 to 3-30, p. 75.
        """
        CL, V1, Q, V2, dose, t_inf = 5.0, 20.0, 3.0, 15.0, 100.0, 4.0
        k10 = CL / V1
        k12 = Q / V1
        k21 = Q / V2
        s1 = k10 + k12 + k21
        disc = math.sqrt(s1 * s1 - 4.0 * k10 * k21)
        alpha = (s1 + disc) / 2.0
        beta = (s1 - disc) / 2.0
        R0 = dose / t_inf
        A_s = (alpha - k21) / (V1 * (alpha - beta))
        B_s = (k21 - beta) / (V1 * (alpha - beta))

        t_mid = 2.0
        C = c_2cmt_iv_infusion([t_mid], dose=dose, CL=CL, V1=V1, Q=Q, V2=V2, t_inf=t_inf)
        expected = R0 * (
            A_s / alpha * (1.0 - math.exp(-alpha * t_mid))
            + B_s / beta * (1.0 - math.exp(-beta * t_mid))
        )
        assert math.isclose(C[0], expected, rel_tol=1e-10)

    def test_continuity_at_t_inf(self) -> None:
        """Profile must be continuous at the end of infusion.

        Reference: by construction -- post-infusion formula evaluated at t_inf must
        equal during-infusion formula at t_inf.
        """
        CL, V1, Q, V2, dose, t_inf = 5.0, 20.0, 3.0, 15.0, 100.0, 2.0
        eps = 1e-7
        C_before = c_2cmt_iv_infusion(
            [t_inf - eps], dose=dose, CL=CL, V1=V1, Q=Q, V2=V2, t_inf=t_inf
        )
        C_after = c_2cmt_iv_infusion(
            [t_inf + eps], dose=dose, CL=CL, V1=V1, Q=Q, V2=V2, t_inf=t_inf
        )
        assert math.isclose(C_before[0], C_after[0], rel_tol=1e-4)

    def test_steady_state_plateau_equals_r0_over_cl(self) -> None:
        """At steady-state (t >> half-lives), C_ss -> R0/CL.

        Reference: derived from alpha*beta = k10*k21 for 2-cmt system;
        C_ss = R0/V1 * k21/(alpha*beta) = R0/CL.
        """
        CL, V1, Q, V2, dose, t_inf = 5.0, 20.0, 3.0, 15.0, 100.0, 200.0
        R0 = dose / t_inf
        C = c_2cmt_iv_infusion([100.0], dose=dose, CL=CL, V1=V1, Q=Q, V2=V2, t_inf=t_inf)
        assert math.isclose(C[0], R0 / CL, rel_tol=1e-3)

    def test_short_infusion_approaches_bolus(self) -> None:
        """Very short infusion converges to IV bolus solution for t >> t_inf.

        Reference: limiting case as t_inf -> 0 (rectangular pulse -> impulse).
        """
        CL, V1, Q, V2, dose = 5.0, 20.0, 3.0, 15.0, 100.0
        t_inf = 1e-4
        t = np.linspace(1.0, 24.0, 50)
        C_inf = c_2cmt_iv_infusion(t, dose=dose, CL=CL, V1=V1, Q=Q, V2=V2, t_inf=t_inf)
        C_bolus = c_2cmt_iv_bolus(t, dose=dose, CL=CL, V1=V1, Q=Q, V2=V2)
        np.testing.assert_allclose(C_inf, C_bolus, rtol=5e-3)

    def test_positive_concentrations(self) -> None:
        """All simulated concentrations must be >= 0."""
        t = np.linspace(0, 48, 200)
        C = c_2cmt_iv_infusion(t, dose=100.0, CL=5.0, V1=20.0, Q=3.0, V2=15.0, t_inf=2.0)
        assert np.all(C >= -1e-12)

    def test_raises_on_invalid_t_inf(self) -> None:
        with pytest.raises(ValueError, match="t_inf must be > 0"):
            c_2cmt_iv_infusion([1.0], dose=100.0, CL=5.0, V1=20.0, Q=3.0, V2=15.0, t_inf=0.0)


# ---------------------------------------------------------------------------
# 2-compartment oral
# ---------------------------------------------------------------------------


class TestC2CmtOral:
    """Tests for c_2cmt_oral."""

    def test_at_t0_is_zero(self) -> None:
        """C(0) = 0 for oral dosing.

        Reference: Gibaldi & Perrier 2nd ed. (1982), Eq. 4-4.
        """
        C = c_2cmt_oral([0.0], dose=100.0, CL_F=5.0, V1_F=20.0, Q=3.0, V2=15.0, ka=1.5)
        assert math.isclose(C[0], 0.0, abs_tol=1e-12)

    def test_three_exponential_coefficients_sum_to_zero(self) -> None:
        """Sum of the three exponential coefficients = 0 (verifies C(0)=0).

        Reference: Gibaldi & Perrier 2nd ed. (1982), Eq. 4-4; derived from
        Laplace transform partial fractions.
        """
        import math as _math

        CL_F, V1_F, Q, V2, ka = 5.0, 20.0, 3.0, 15.0, 1.5
        k10 = CL_F / V1_F
        k12 = Q / V1_F
        k21 = Q / V2
        s1 = k10 + k12 + k21
        disc = _math.sqrt(s1 * s1 - 4 * k10 * k21)
        alpha = (s1 + disc) / 2.0
        beta = (s1 - disc) / 2.0

        coeff_alpha = (k21 - alpha) / ((beta - alpha) * (ka - alpha))
        coeff_beta = (k21 - beta) / ((alpha - beta) * (ka - beta))
        coeff_ka = (k21 - ka) / ((alpha - ka) * (beta - ka))

        total = coeff_alpha + coeff_beta + coeff_ka
        assert math.isclose(total, 0.0, abs_tol=1e-12)

    def test_positive_concentrations_on_upswing(self) -> None:
        """All simulated concentrations must be >= 0 (within machine epsilon at t=0)."""
        t = np.linspace(0, 48, 200)
        C = c_2cmt_oral(t, dose=100.0, CL_F=5.0, V1_F=20.0, Q=3.0, V2=15.0, ka=1.5)
        # At t=0, the three-exponential coefficients sum to zero but floating point
        # arithmetic can produce a residual of ~1e-15. Accept abs_tol for that point.
        assert np.all(C >= -1e-12)

    def test_raises_ka_equal_to_alpha(self) -> None:
        """Raises ValueError when ka is numerically equal to alpha."""
        # Force ka to equal the computed alpha by reverse engineering
        CL_F, V1_F, Q, V2 = 5.0, 20.0, 3.0, 15.0
        k10 = CL_F / V1_F
        k12 = Q / V1_F
        k21 = Q / V2
        s1 = k10 + k12 + k21
        disc = math.sqrt(s1 * s1 - 4 * k10 * k21)
        alpha = (s1 + disc) / 2.0
        with pytest.raises(ValueError, match="numerically equal to alpha"):
            c_2cmt_oral([1.0], dose=100.0, CL_F=CL_F, V1_F=V1_F, Q=Q, V2=V2, ka=alpha)


# ---------------------------------------------------------------------------
# Superposition
# ---------------------------------------------------------------------------


class TestSuperpose:
    """Tests for superpose()."""

    def test_single_dose_matches_direct(self) -> None:
        """Superposition with one dose equals the direct function call.

        Reference: by construction -- superposition with N=1.
        """
        CL, Vz, dose = 5.0, 20.0, 100.0
        t = np.linspace(0, 24, 100)

        def unit_fn(tr: np.ndarray, d: float) -> np.ndarray:
            return c_1cmt_iv_bolus(tr, d, CL=CL, Vz=Vz)

        C_super = superpose(t, [0.0], [dose], unit_fn)
        C_direct = c_1cmt_iv_bolus(t, dose, CL=CL, Vz=Vz)
        np.testing.assert_allclose(C_super, C_direct, rtol=1e-12)

    def test_two_dose_superposition(self) -> None:
        """Superposition of two doses equals sum of individual contributions.

        Reference: linear system superposition principle.
        """
        CL, Vz = 5.0, 20.0
        dose1, dose2 = 100.0, 80.0
        t1, t2 = 0.0, 12.0
        t = np.linspace(0, 24, 200)

        def unit_fn(tr: np.ndarray, d: float) -> np.ndarray:
            return c_1cmt_iv_bolus(tr, d, CL=CL, Vz=Vz)

        C_super = superpose(t, [t1, t2], [dose1, dose2], unit_fn)

        # Manual: dose1 at t>=0, dose2 at t>=t2
        C1 = c_1cmt_iv_bolus(t, dose1, CL=CL, Vz=Vz)
        # Only evaluate dose2 contribution on the subset where t >= t2
        t_rel2 = t - t2
        C2 = np.zeros_like(t)
        mask2 = t_rel2 >= 0.0
        if mask2.any():
            C2[mask2] = c_1cmt_iv_bolus(t_rel2[mask2], dose2, CL=CL, Vz=Vz)
        np.testing.assert_allclose(C_super, C1 + C2, rtol=1e-12)

    def test_pre_dose_times_are_zero(self) -> None:
        """Times before first dose produce zero concentration."""
        CL, Vz, dose = 5.0, 20.0, 100.0
        t = np.array([-1.0, 0.0, 1.0])

        def unit_fn(tr: np.ndarray, d: float) -> np.ndarray:
            return c_1cmt_iv_bolus(tr, d, CL=CL, Vz=Vz)

        # superpose doesn't validate negative times -- that's _prepare_times's job
        # but with dose at t=0, t < 0 contributes nothing
        C = superpose(t, [0.0], [dose], unit_fn)
        assert C[0] == 0.0  # t=-1 < dose_time=0
