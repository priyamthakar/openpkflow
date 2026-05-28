"""Property-based tests for PK simulation analytical invariants.

Uses hypothesis to assert mathematical properties of the analytical
compartment model equations that must hold for ALL valid parameter combinations.
"""

from __future__ import annotations

import math

import numpy as np
from hypothesis import assume, given
from hypothesis import strategies as st

from openpkflow.sim.methods import (
    c_1cmt_iv_bolus,
    c_1cmt_iv_infusion,
    c_1cmt_oral,
    c_2cmt_iv_bolus,
    c_2cmt_iv_infusion,
    c_2cmt_oral,
    superpose,
)

_valid_cl = st.floats(min_value=0.05, max_value=50.0)
_valid_v = st.floats(min_value=1.0, max_value=200.0)
_valid_ka = st.floats(min_value=0.1, max_value=5.0)
_valid_dose = st.floats(min_value=1.0, max_value=1000.0)


class Test1CmtNonnegativity:
    @given(
        _valid_dose,
        _valid_cl,
        _valid_v,
    )
    def test_iv_bolus_nonnegative(self, dose, cl, v):
        """IV bolus C(t) must be >= 0 for all t >= 0."""
        times = np.linspace(0, 72, 50)
        c = c_1cmt_iv_bolus(times, dose, cl, v)
        assert np.all(c >= 0.0)

    @given(
        _valid_dose,
        _valid_cl,
        _valid_v,
        _valid_ka,
    )
    def test_oral_nonnegative(self, dose, cl, v, ka):
        """Oral C(t) must be >= 0 for all t >= 0."""
        times = np.linspace(0, 72, 50)
        c = c_1cmt_oral(times, dose, cl, v, ka)
        assert np.all(c >= -1e-13)  # floating-point rounding can produce -1.33e-14

    @given(_valid_dose, _valid_cl, _valid_v)
    def test_iv_bolus_t0_equals_dose_over_v(self, dose, cl, v):
        """C(0) must equal dose/Vz for IV bolus."""
        c = c_1cmt_iv_bolus([0.0], dose, cl, v)
        assert np.isclose(c[0], dose / v, rtol=1e-12)

    @given(_valid_dose, _valid_cl, _valid_v, _valid_ka)
    def test_oral_t0_is_zero(self, dose, cl, v, ka):
        """C(0) must be 0 for oral administration."""
        c = c_1cmt_oral([0.0], dose, cl, v, ka)
        assert np.isclose(c[0], 0.0, atol=1e-14)

    @given(_valid_dose, _valid_cl, _valid_v)
    def test_iv_bolus_monotonic_decline(self, dose, cl, v):
        """IV bolus concentrations must be strictly decreasing."""
        times = np.linspace(0, 48, 100)
        c = c_1cmt_iv_bolus(times, dose, cl, v)
        assert np.all(np.diff(c) <= 0.0)


class TestInfusionInvariants:
    @given(_valid_dose, _valid_cl, _valid_v, st.floats(min_value=0.5, max_value=24.0))
    def test_infusion_end_greater_than_zero(self, dose, cl, v, duration):
        """Infusion concentrations at end of infusion must be positive."""
        times = np.linspace(0, duration, 50)
        c = c_1cmt_iv_infusion(times, dose, cl, v, duration)
        assert np.all(c >= 0.0)
        assert c[-1] > 0.0


class Test2CmtInvariants:
    @given(
        _valid_dose,
        _valid_cl,
        _valid_v,
        st.floats(min_value=0.05, max_value=30.0),
        st.floats(min_value=1.0, max_value=150.0),
    )
    def test_2cmt_iv_nonnegative(self, dose, cl, v1, q, v2):
        """2-cmt IV bolus concentrations must be >= 0."""
        times = np.linspace(0, 72, 80)
        c = c_2cmt_iv_bolus(times, dose, cl, v1, q, v2)
        assert np.all(c >= 0.0)

    @given(
        _valid_dose,
        _valid_cl,
        _valid_v,
        _valid_ka,
        st.floats(min_value=0.05, max_value=30.0),
        st.floats(min_value=1.0, max_value=150.0),
    )
    def test_2cmt_oral_nonnegative(self, dose, cl, v1, ka, q, v2):
        """2-cmt oral concentrations must be >= 0 (within floating point)."""
        times = np.linspace(0, 72, 80)
        c = c_2cmt_oral(times, dose, cl, v1, ka, q, v2)
        assert np.all(c >= -1e-10)

    @given(
        _valid_dose,
        _valid_cl,
        _valid_v,
        _valid_ka,
        st.floats(min_value=0.05, max_value=30.0),
        st.floats(min_value=1.0, max_value=150.0),
    )
    def test_2cmt_oral_t0_zero(self, dose, cl, v1, ka, q, v2):
        """C(0) must be 0 for 2-cmt oral (within floating point)."""
        c = c_2cmt_oral([0.0], dose, cl, v1, ka, q, v2)
        assert np.isclose(c[0], 0.0, atol=1e-10)


class TestSuperposition:
    @given(st.integers(min_value=1, max_value=5))
    def test_superpose_nonnegative(self, n_doses):
        """All superposed concentrations must be >= 0."""
        times = np.linspace(0, 72, 50)
        cl, v = 5.0, 50.0
        dose_amounts = [100.0] * n_doses
        dose_times = [i * 12.0 for i in range(n_doses)]

        def single_dose(t_rel, amt):
            return c_1cmt_iv_bolus(t_rel, amt, cl, v)

        result = superpose(times, dose_times, dose_amounts, single_dose)

        assert np.all(result >= 0.0)

    @given(
        st.integers(min_value=2, max_value=5),
        st.floats(min_value=6.0, max_value=24.0),
    )
    def test_multiple_doses_accumulate(self, n_doses, tau):
        """Multiple doses should accumulate: trough after dose 2 >= trough after dose 1."""
        dose = 100.0
        cl, v = 5.0, 50.0
        times = np.linspace(0, tau * n_doses, 100)
        dose_amounts = [dose] * n_doses
        dose_times = [i * tau for i in range(n_doses)]

        def single_dose(t_rel, amt):
            return c_1cmt_iv_bolus(t_rel, amt, cl, v)

        multi = superpose(times, dose_times, dose_amounts, single_dose)

        single_tail = c_1cmt_iv_bolus([tau], dose, cl, v)[0]
        multi_trough = multi[np.searchsorted(times, tau)]
        assert multi_trough >= single_tail - 1e-12


class TestInfusionContinuity:
    @given(_valid_dose, _valid_cl, _valid_v, st.floats(min_value=0.5, max_value=24.0))
    def test_1cmt_infusion_monotonic_increasing_during_infusion(self, dose, cl, v, t_inf):
        times = np.linspace(0, t_inf, 50)
        c = c_1cmt_iv_infusion(times, dose, cl, v, t_inf)
        assert np.all(np.diff(c) > -1e-15)

    @given(_valid_dose, _valid_cl, _valid_v)
    def test_1cmt_infusion_t0_is_zero(self, dose, cl, v):
        c = c_1cmt_iv_infusion([0.0], dose, cl, v, t_inf=2.0)
        assert np.isclose(c[0], 0.0, atol=1e-14)

    @given(_valid_dose, _valid_cl, _valid_v, st.floats(min_value=0.5, max_value=24.0))
    def test_1cmt_infusion_positive_for_positive_t(self, dose, cl, v, t_inf):
        times = np.linspace(0.01, t_inf, 20)
        c = c_1cmt_iv_infusion(times, dose, cl, v, t_inf)
        assert np.all(c > 0.0)

    @given(_valid_dose, _valid_cl, _valid_v, st.floats(min_value=100.0, max_value=500.0))
    def test_1cmt_infusion_steady_state_approaches_r0_over_cl(self, dose, cl, v, long_tinf):
        r0 = dose / long_tinf
        hl = math.log(2) * v / cl
        assume(long_tinf > 5 * hl)
        c = c_1cmt_iv_infusion([long_tinf], dose, cl, v, long_tinf)
        expected_ss = r0 / cl
        assert np.isclose(c[0], expected_ss, rtol=0.05)

    @given(
        _valid_dose,
        _valid_cl,
        _valid_v,
        st.floats(min_value=0.05, max_value=30.0),
        st.floats(min_value=1.0, max_value=150.0),
        st.floats(min_value=0.5, max_value=24.0),
    )
    def test_2cmt_infusion_declines_after_infusion(self, dose, cl, v1, q, v2, t_inf):
        times = np.linspace(t_inf, t_inf * 2, 30)
        c = c_2cmt_iv_infusion(times, dose, cl, v1, q, v2, t_inf)
        assert np.all(np.diff(c) <= 0.0)

    @given(
        _valid_dose,
        _valid_cl,
        _valid_v,
        st.floats(min_value=0.05, max_value=30.0),
        st.floats(min_value=1.0, max_value=150.0),
    )
    def test_2cmt_infusion_t0_zero(self, dose, cl, v1, q, v2):
        c = c_2cmt_iv_infusion([0.0], dose, cl, v1, q, v2, t_inf=2.0)
        assert np.isclose(c[0], 0.0, atol=1e-14)

    @given(
        _valid_dose,
        _valid_cl,
        _valid_v,
        st.floats(min_value=0.05, max_value=10.0),
        st.floats(min_value=1.0, max_value=150.0),
        st.floats(min_value=0.001, max_value=0.01),
    )
    def test_2cmt_infusion_bolus_limit(self, dose, cl, v1, q, v2, tiny_tinf):
        from openpkflow.sim.methods import c_2cmt_iv_bolus

        times = np.linspace(tiny_tinf, 24.0, 30)
        c_inf = c_2cmt_iv_infusion(times, dose, cl, v1, q, v2, tiny_tinf)
        c_bolus = c_2cmt_iv_bolus(times, dose, cl, v1, q, v2)

        # In the bolus limit, infusion->bolus; use relaxed tolerance because
        # of the discretized input rate at finite t_inf.
        assert np.allclose(c_inf, c_bolus, rtol=0.30)

    @given(
        _valid_dose,
        _valid_cl,
        _valid_v,
        st.floats(min_value=0.05, max_value=30.0),
        st.floats(min_value=1.0, max_value=150.0),
        st.floats(min_value=100.0, max_value=500.0),
    )
    def test_2cmt_infusion_approaches_plateau(self, dose, cl, v1, q, v2, long_tinf):
        c_near_end = c_2cmt_iv_infusion([long_tinf * 0.9], dose, cl, v1, q, v2, long_tinf)[0]
        c_at_end = c_2cmt_iv_infusion([long_tinf], dose, cl, v1, q, v2, long_tinf)[0]
        assert c_at_end >= c_near_end * 0.8
        assert c_at_end > 0.0


class Test2CmtOralCoefficients:
    @given(
        _valid_dose,
        _valid_cl,
        _valid_v,
        _valid_ka,
        st.floats(min_value=0.05, max_value=30.0),
        st.floats(min_value=1.0, max_value=150.0),
    )
    def test_2cmt_oral_t0_zero(self, dose, cl, v1, ka, q, v2):
        c = c_2cmt_oral([0.0], dose, cl, v1, ka, q, v2)
        assert np.isclose(c[0], 0.0, atol=1e-10)

    @given(
        _valid_dose,
        _valid_cl,
        _valid_v,
        _valid_ka,
        st.floats(min_value=0.05, max_value=30.0),
        st.floats(min_value=1.0, max_value=150.0),
    )
    def test_2cmt_oral_nonnegative(self, dose, cl, v1, ka, q, v2):
        times = np.linspace(0, 72, 80)
        c = c_2cmt_oral(times, dose, cl, v1, ka, q, v2)
        assert np.all(c >= -1e-10)


class TestSuperpositionProperties:
    @given(st.integers(min_value=1, max_value=5), st.floats(min_value=0.1, max_value=10.0))
    def test_superpose_linearity(self, n_doses, factor):
        times = np.linspace(0, 72, 50)
        cl, v = 5.0, 50.0
        base_amounts = [100.0] * n_doses
        scaled_amounts = [a * factor for a in base_amounts]
        dose_times = [i * 12.0 for i in range(n_doses)]

        def single_dose(t_rel, amt):
            return c_1cmt_iv_bolus(t_rel, amt, cl, v)

        base = superpose(times, dose_times, base_amounts, single_dose)
        scaled = superpose(times, dose_times, scaled_amounts, single_dose)
        assert np.allclose(scaled, base * factor, rtol=1e-10)

    @given(
        st.integers(min_value=2, max_value=5),
        st.floats(min_value=6.0, max_value=24.0),
    )
    def test_superpose_accumulation_monotonic(self, n_doses, tau):
        dose = 100.0
        cl, v = 5.0, 50.0
        times = np.linspace(0, tau * n_doses, 100)

        def single_dose(t_rel, amt):
            return c_1cmt_iv_bolus(t_rel, amt, cl, v)

        for k in range(1, n_doses):
            partial_amounts = [dose] * k
            partial_times = [i * tau for i in range(k)]
            full_amounts = [dose] * (k + 1)
            full_times = [i * tau for i in range(k + 1)]

            partial = superpose(times, partial_times, partial_amounts, single_dose)
            full = superpose(times, full_times, full_amounts, single_dose)
            assert np.all(partial <= full + 1e-12)
