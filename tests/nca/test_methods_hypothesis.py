"""Property-based tests for NCA mathematical invariants.

Uses hypothesis to assert correctness properties that should hold for
ALL valid inputs, not just hand-picked test cases.
"""

from __future__ import annotations

import math

import numpy as np
from hypothesis import assume, given
from hypothesis import strategies as st

from openpkflow.nca.methods import (
    accumulation_ratio,
    auc_inf_obs,
    auc_linear,
    auc_linear_up_log_down,
    auc_log,
    auc_percent_extrapolated,
    clearance_volume_parameters,
    cmax,
    cumulative_urinary_excretion,
    lambda_z,
    percent_excreted,
    renal_clearance,
    steady_state_parameters,
    tmax,
)


def _valid_conc() -> st.SearchStrategy[list[float]]:
    return st.lists(st.floats(min_value=0.0, max_value=1000.0), min_size=2, max_size=50)


def _valid_times() -> st.SearchStrategy[list[float]]:
    return st.lists(
        st.floats(min_value=0.0, max_value=168.0, allow_nan=False, allow_infinity=False),
        min_size=2,
        max_size=50,
        unique=True,
    ).map(lambda lst: sorted(lst))


class TestAUCLinearInvariants:
    @given(st.lists(st.floats(min_value=0.0, max_value=1000.0), min_size=2, max_size=30))
    def test_nonnegative(self, conc):
        """Linear AUC must be >= 0 for non-negative concentrations."""
        times = sorted([float(i) for i in range(len(conc))])
        result = auc_linear(times, conc)
        assert result >= 0.0

    @given(st.lists(st.floats(min_value=0.0, max_value=1000.0), min_size=2, max_size=30))
    def test_all_zeros(self, conc):
        """Linear AUC must be exactly 0 when all concentrations are zero."""
        times = sorted([float(i) for i in range(len(conc))])
        conc_zero = [0.0] * len(conc)
        assert auc_linear(times, conc_zero) == 0.0

    @given(
        st.lists(
            st.floats(
                min_value=0.0,
                max_value=1000.0,
                allow_subnormal=False,
            ),
            min_size=2,
            max_size=30,
        ),
        st.floats(min_value=0.1, max_value=10.0),
    )
    def test_scale_invariance(self, conc, factor):
        """Scaling all concentrations by a constant scales AUC by the same constant."""
        times = sorted([float(i) for i in range(len(conc))])
        original = auc_linear(times, conc)
        scaled = auc_linear(times, [c * factor for c in conc])
        if original == 0:
            assert scaled == 0.0
        else:
            assert np.isclose(scaled / original, factor, rtol=1e-12)

    def test_subnormal_scaling_underflows_at_float_boundary(self):
        """Smallest subnormal concentrations can underflow when scaled."""
        smallest_subnormal = np.nextafter(0.0, 1.0)
        original = auc_linear([0.0, 1.0], [smallest_subnormal, smallest_subnormal])
        scaled = auc_linear(
            [0.0, 1.0],
            [smallest_subnormal * 0.5, smallest_subnormal * 0.5],
        )

        assert original == smallest_subnormal
        assert scaled == 0.0


class TestAUCAllMethods:
    @given(
        st.lists(st.floats(min_value=0.01, max_value=1000.0), min_size=3, max_size=30),
        st.floats(min_value=0.1, max_value=10.0),
    )
    def test_scale_linearity(self, conc, factor):
        """All AUC methods should scale approximately linearly with concentration."""
        times = sorted([float(i) for i in range(len(conc))])

        for auc_fn in [auc_linear, auc_log, auc_linear_up_log_down]:
            original = auc_fn(times, conc)
            scaled = auc_fn(times, [c * factor for c in conc])

            orig_val = original.value if hasattr(original, "value") else original
            scaled_val = scaled.value if hasattr(scaled, "value") else scaled

            if orig_val == 0:
                assert scaled_val == 0.0
            else:
                assert np.isclose(scaled_val / orig_val, factor, rtol=1e-6)


class TestCmaxTmax:
    @given(
        st.lists(st.floats(min_value=0.0, max_value=1000.0), min_size=1, max_size=50),
    )
    def test_cmax_nonnegative(self, conc):
        """Cmax must be >= 0 for non-negative concentrations."""
        result = cmax(conc)
        assert result >= 0.0

    @given(
        st.lists(st.floats(min_value=0.0, max_value=1000.0), min_size=1, max_size=50),
    )
    def test_cmax_at_least_every_concentration(self, conc):
        """Cmax must be >= every individual concentration."""
        result = cmax(conc)
        for c in conc:
            assert result >= c

    @given(
        st.lists(st.floats(min_value=0.0, max_value=1000.0), min_size=1, max_size=50),
    )
    def test_tmax_in_times(self, conc):
        """Tmax must be one of the input times."""
        times = [float(i) for i in range(len(conc))]
        result = tmax(times, conc)
        assert result in times

    @given(
        st.lists(st.floats(min_value=0.0, max_value=1000.0), min_size=1, max_size=50),
    )
    def test_cmax_equals_at_tmax(self, conc):
        """Concentration at tmax must equal cmax."""
        times = [float(i) for i in range(len(conc))]
        t_val = tmax(times, conc)
        c_val = cmax(conc)
        idx = times.index(t_val)
        assert np.isclose(conc[idx], c_val)


class TestAUCLinearUpLogDown:
    @given(
        st.lists(st.floats(min_value=0.001, max_value=100.0), min_size=4, max_size=20),
    )
    def test_monotonic_decline(self, conc):
        """For strictly declining positive conc, log rule result >= 0."""
        conc = sorted(conc, reverse=True)
        times = [float(i) for i in range(len(conc))]
        result = auc_linear_up_log_down(times, conc)
        assert result.value >= 0.0

    @given(
        st.lists(st.floats(min_value=0.001, max_value=100.0), min_size=3, max_size=20),
    )
    def test_log_rule_nonnegative(self, conc):
        """When all points are positive and declining, result is nonnegative."""
        conc = sorted(conc, reverse=True)
        times = [float(i) for i in range(len(conc))]
        result = auc_linear_up_log_down(times, conc)
        assert result.value >= 0.0


class TestAUCLogInvariants:
    @given(
        st.lists(st.floats(min_value=0.1, max_value=1000.0), min_size=3, max_size=20),
        st.floats(min_value=0.1, max_value=10.0),
    )
    def test_auc_log_scale_invariance(self, conc, factor):
        times = sorted([float(i) for i in range(len(conc))])
        assume(all(abs(a - b) > 1e-10 for a, b in zip(conc, conc[1:], strict=False)))
        orig = auc_log(times, conc).value
        scaled = auc_log(times, [c * factor for c in conc]).value
        if orig == 0:
            assert scaled == 0.0
        else:
            assert np.isclose(scaled / orig, factor, rtol=1e-10)

    @given(
        st.lists(
            st.floats(min_value=0.0, max_value=100.0, allow_subnormal=False),
            min_size=3,
            max_size=20,
        ),
    )
    def test_auc_log_nonnegative(self, conc):
        times = sorted([float(i) for i in range(len(conc))])
        result = auc_log(times, conc)
        assert result.value >= 0.0

    @given(
        st.lists(st.floats(min_value=0.1, max_value=100.0), min_size=4, max_size=20),
    )
    def test_all_declining_no_warnings(self, conc):
        conc = sorted(conc, reverse=True)
        assume(len(set(conc)) == len(conc))
        times = [float(i) for i in range(len(conc))]
        result = auc_log(times, conc)
        assert len(result.warnings) == 0

    @given(
        st.lists(
            st.floats(min_value=0.0, max_value=100.0, allow_subnormal=False),
            min_size=3,
            max_size=15,
        ),
    )
    def test_fallback_count_correct(self, conc):
        times = sorted([float(i) for i in range(len(conc))])
        result = auc_log(times, conc)
        expected_fallbacks = 0
        for i in range(len(conc) - 1):
            if conc[i] <= 0.0 or conc[i + 1] <= 0.0 or conc[i] == conc[i + 1]:
                expected_fallbacks += 1
        assert len(result.warnings) == expected_fallbacks


class TestAUCInfObs:
    @given(
        st.floats(min_value=1.0, max_value=1000.0),
        st.floats(min_value=0.1, max_value=50.0),
        st.floats(min_value=0.01, max_value=1.0),
    )
    def test_monotonic_in_auclast(self, auclast, clast, lz):
        from openpkflow.nca.methods import LambdaZResult

        lz_res = LambdaZResult(
            lambda_z=lz,
            half_life=math.log(2) / lz,
            intercept=0.0,
            r_squared=0.95,
            adj_r_squared=0.93,
            n_points=3,
            time_start=0.0,
            time_end=10.0,
            selected_times=[0.0],
            selected_concs=[clast],
            method="auto",
        )
        a1 = auc_inf_obs(auclast, clast, lz_res)
        a2 = auc_inf_obs(auclast + 1.0, clast, lz_res)
        assert a2 > a1

    @given(
        st.floats(min_value=1.0, max_value=500.0),
        st.floats(min_value=0.1, max_value=50.0),
        st.floats(min_value=0.02, max_value=0.5),
        st.floats(min_value=0.51, max_value=1.0),
    )
    def test_monotonic_in_one_over_lambda_z(self, auclast, clast, lz_low, lz_high):
        from openpkflow.nca.methods import LambdaZResult

        assume(lz_high > lz_low)
        lz_res_low = LambdaZResult(
            lambda_z=lz_low,
            half_life=math.log(2) / lz_low,
            intercept=0.0,
            r_squared=0.95,
            adj_r_squared=0.93,
            n_points=3,
            time_start=0.0,
            time_end=10.0,
            selected_times=[0.0],
            selected_concs=[clast],
            method="auto",
        )
        lz_res_high = LambdaZResult(
            lambda_z=lz_high,
            half_life=math.log(2) / lz_high,
            intercept=0.0,
            r_squared=0.95,
            adj_r_squared=0.93,
            n_points=3,
            time_start=0.0,
            time_end=10.0,
            selected_times=[0.0],
            selected_concs=[clast],
            method="auto",
        )
        a_low = auc_inf_obs(auclast, clast, lz_res_low)
        a_high = auc_inf_obs(auclast, clast, lz_res_high)
        assert a_low >= a_high

    @given(
        st.floats(min_value=1.0, max_value=500.0),
        st.floats(min_value=0.01, max_value=1.0),
    )
    def test_clast_zero_yields_aucinf_equals_auclast(self, auclast, lz):
        from openpkflow.nca.methods import LambdaZResult

        lz_res = LambdaZResult(
            lambda_z=lz,
            half_life=math.log(2) / lz,
            intercept=0.0,
            r_squared=0.95,
            adj_r_squared=0.93,
            n_points=3,
            time_start=0.0,
            time_end=10.0,
            selected_times=[0.0],
            selected_concs=[0.0],
            method="auto",
        )
        result = auc_inf_obs(auclast, 0.0, lz_res)
        assert np.isclose(result, auclast, rtol=1e-10)


class TestAUCPctExtrapolated:
    @given(
        st.floats(min_value=0.1, max_value=500.0),
        st.floats(min_value=0.1, max_value=1000.0),
    )
    def test_in_0_to_100_range(self, auclast, aucinf):
        assume(auclast <= aucinf)
        result = auc_percent_extrapolated(auclast, aucinf)
        assert 0.0 <= result <= 100.0 + 1e-10

    @given(
        st.floats(min_value=0.0, max_value=500.0),
        st.floats(min_value=0.1, max_value=1000.0),
    )
    def test_nonnegative_when_auclast_le_aucinf(self, auclast, aucinf):
        assume(auclast <= aucinf)
        result = auc_percent_extrapolated(auclast, aucinf)
        assert result >= 0.0

    @given(st.floats(min_value=0.1, max_value=1000.0))
    def test_zero_pct_when_auclast_equals_aucinf(self, val):
        result = auc_percent_extrapolated(val, val)
        assert np.isclose(result, 0.0, atol=1e-12)

    @given(st.floats(min_value=0.1, max_value=1000.0))
    def test_hundred_pct_when_auclast_zero(self, aucinf):
        result = auc_percent_extrapolated(0.0, aucinf)
        assert np.isclose(result, 100.0, atol=1e-12)


class TestClearanceVolume:
    @given(
        st.floats(min_value=1.0, max_value=1000.0),
        st.floats(min_value=1.0, max_value=500.0),
        st.floats(min_value=0.01, max_value=1.0),
    )
    def test_cl_equals_dose_over_aucinf_iv(self, dose, aucinf, lz):
        from openpkflow.nca.methods import LambdaZResult

        lz_res = LambdaZResult(
            lambda_z=lz,
            half_life=math.log(2) / lz,
            intercept=0.0,
            r_squared=0.95,
            adj_r_squared=0.93,
            n_points=3,
            time_start=0.0,
            time_end=10.0,
            selected_times=[0.0],
            selected_concs=[1.0],
            method="auto",
        )
        result = clearance_volume_parameters(dose, aucinf, lz_res, route="iv_bolus")
        assert np.isclose(result["CL"], dose / aucinf, rtol=1e-10)
        assert np.isclose(result["Vz"], dose / (aucinf * lz), rtol=1e-10)

    @given(
        st.floats(min_value=1.0, max_value=1000.0),
        st.floats(min_value=1.0, max_value=500.0),
        st.floats(min_value=0.01, max_value=1.0),
    )
    def test_cl_f_equals_dose_over_aucinf_oral(self, dose, aucinf, lz):
        from openpkflow.nca.methods import LambdaZResult

        lz_res = LambdaZResult(
            lambda_z=lz,
            half_life=math.log(2) / lz,
            intercept=0.0,
            r_squared=0.95,
            adj_r_squared=0.93,
            n_points=3,
            time_start=0.0,
            time_end=10.0,
            selected_times=[0.0],
            selected_concs=[1.0],
            method="auto",
        )
        result = clearance_volume_parameters(dose, aucinf, lz_res, route="oral")
        assert "CL_F" in result and "Vz_F" in result
        assert np.isclose(result["CL_F"], dose / aucinf, rtol=1e-10)

    @given(
        st.floats(min_value=1.0, max_value=1000.0),
        st.floats(min_value=1.0, max_value=500.0),
        st.floats(min_value=0.01, max_value=1.0),
    )
    def test_iv_routes_produce_cl_not_cl_f(self, dose, aucinf, lz):
        from openpkflow.nca.methods import LambdaZResult

        lz_res = LambdaZResult(
            lambda_z=lz,
            half_life=math.log(2) / lz,
            intercept=0.0,
            r_squared=0.95,
            adj_r_squared=0.93,
            n_points=3,
            time_start=0.0,
            time_end=10.0,
            selected_times=[0.0],
            selected_concs=[1.0],
            method="auto",
        )
        result = clearance_volume_parameters(dose, aucinf, lz_res, route="iv_bolus")
        assert "CL" in result and "Vz" in result
        assert "CL_F" not in result and "Vz_F" not in result


class TestSteadyState:
    @given(
        st.lists(st.floats(min_value=0.1, max_value=100.0), min_size=3, max_size=20),
        st.floats(min_value=1.0, max_value=24.0),
    )
    def test_cmax_ss_ge_cmin_ss(self, conc, tau):
        times = [float(i) / len(conc) * tau for i in range(len(conc))]
        result = steady_state_parameters(times, conc, tau=tau, auc_method="linear")
        assert result["Cmax_ss"] >= result["Cmin_ss"]

    @given(
        st.lists(st.floats(min_value=0.1, max_value=100.0), min_size=3, max_size=20),
        st.floats(min_value=1.0, max_value=24.0),
    )
    def test_fluctuation_nonnegative(self, conc, tau):
        times = [float(i) / len(conc) * tau for i in range(len(conc))]
        result = steady_state_parameters(times, conc, tau=tau, auc_method="linear")
        assert result["fluctuation_pct"] >= 0.0

    @given(
        st.lists(st.floats(min_value=0.1, max_value=100.0), min_size=3, max_size=20),
        st.floats(min_value=1.0, max_value=24.0),
    )
    def test_swing_nonnegative_when_cmin_positive(self, conc, tau):
        times = [float(i) / len(conc) * tau for i in range(len(conc))]
        result = steady_state_parameters(times, conc, tau=tau, auc_method="linear")
        if result["Cmin_ss"] > 0:
            assert result["swing"] >= 0.0

    @given(
        st.lists(st.floats(min_value=0.1, max_value=100.0), min_size=3, max_size=20),
        st.floats(min_value=1.0, max_value=24.0),
    )
    def test_cavg_ss_equals_auctau_over_tau(self, conc, tau):
        times = [float(i) / len(conc) * tau for i in range(len(conc))]
        result = steady_state_parameters(times, conc, tau=tau, auc_method="linear")
        assert np.isclose(result["Cavg_ss"], result["AUCtau"] / tau, rtol=1e-10)

    def test_cmin_zero_swing_is_none(self):
        result = steady_state_parameters(
            [0.0, 4.0, 8.0, 12.0], [10.0, 5.0, 0.0, 0.0], tau=12.0, auc_method="linear"
        )
        assert result["swing"] is None


class TestAccumulationRatio:
    @given(
        st.floats(min_value=0.1, max_value=500.0),
        st.floats(min_value=0.1, max_value=500.0),
    )
    def test_ratio_nonnegative(self, auctau_ss, auctau_sd):
        result = accumulation_ratio(auctau_ss, auctau_sd)
        assert result >= 0.0

    @given(st.floats(min_value=0.1, max_value=500.0))
    def test_equal_auctau_yields_one(self, auctau):
        result = accumulation_ratio(auctau, auctau)
        assert np.isclose(result, 1.0, rtol=1e-12)

    @given(
        st.floats(min_value=1.0, max_value=500.0),
        st.floats(min_value=0.1, max_value=1.0),
    )
    def test_monotonic_in_auctau_ss(self, auctau_sd, auctau_ss_low):
        assume(auctau_ss_low + 10.0 <= 500.0)
        auctau_ss_high = auctau_ss_low + 10.0
        r_low = accumulation_ratio(auctau_ss_low, auctau_sd)
        r_high = accumulation_ratio(auctau_ss_high, auctau_sd)
        assert r_high >= r_low


class TestUrinaryExcretion:
    @given(
        st.lists(st.floats(min_value=0.0, max_value=500.0), min_size=2, max_size=20),
        st.lists(st.floats(min_value=0.0, max_value=10.0), min_size=2, max_size=20),
    )
    def test_non_decreasing(self, volumes, concentrations):
        n = min(len(volumes), len(concentrations))
        times = sorted([float(i) for i in range(n)])
        result = cumulative_urinary_excretion(times, volumes[:n], concentrations[:n])
        assert np.all(np.diff(result) >= -1e-12)

    @given(
        st.lists(st.floats(min_value=0.0, max_value=500.0), min_size=2, max_size=20),
        st.lists(st.floats(min_value=0.0, max_value=10.0), min_size=2, max_size=20),
    )
    def test_nonnegative(self, volumes, concentrations):
        n = min(len(volumes), len(concentrations))
        times = sorted([float(i) for i in range(n)])
        result = cumulative_urinary_excretion(times, volumes[:n], concentrations[:n])
        assert np.all(result >= 0.0)

    def test_zero_input_yields_zeros(self):
        result = cumulative_urinary_excretion([0.0, 1.0, 2.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0])
        assert np.all(result == 0.0)


class TestRenalClearance:
    @given(
        st.floats(min_value=0.0, max_value=500.0),
        st.floats(min_value=0.1, max_value=1000.0),
    )
    def test_nonnegative(self, total_ae, auc_inf):
        result = renal_clearance(total_ae, auc_inf)
        assert result >= 0.0

    @given(
        st.floats(min_value=1.0, max_value=500.0),
        st.floats(min_value=0.1, max_value=1000.0),
        st.floats(min_value=0.1, max_value=10.0),
    )
    def test_proportional_to_ae(self, ae_low, auc_inf, factor):
        assume(ae_low * factor <= 500.0)
        ae_high = ae_low * factor
        r_low = renal_clearance(ae_low, auc_inf)
        r_high = renal_clearance(ae_high, auc_inf)
        assert np.isclose(r_high / r_low, factor, rtol=1e-10)

    @given(
        st.floats(min_value=1.0, max_value=500.0),
        st.floats(min_value=0.1, max_value=500.0),
        st.floats(min_value=0.1, max_value=10.0),
    )
    def test_inversely_proportional_to_auc(self, total_ae, auc_low, factor):
        assume(auc_low * factor <= 1000.0)
        auc_high = auc_low * factor
        r_low = renal_clearance(total_ae, auc_low)
        r_high = renal_clearance(total_ae, auc_high)
        assert np.isclose(r_low / r_high, factor, rtol=1e-10)


class TestPercentExcreted:
    @given(
        st.floats(min_value=0.0, max_value=100.0),
        st.floats(min_value=100.0, max_value=500.0),
    )
    def test_nonnegative(self, total_ae, dose):
        result = percent_excreted(total_ae, dose)
        assert result >= 0.0

    @given(
        st.floats(min_value=0.1, max_value=100.0),
        st.floats(min_value=100.0, max_value=500.0),
    )
    def test_ae_le_dose_yields_lt_100(self, total_ae, dose):
        assume(total_ae <= dose)
        result = percent_excreted(total_ae, dose)
        assert result <= 100.0

    @given(
        st.floats(min_value=0.0, max_value=100.0),
        st.floats(min_value=100.0, max_value=500.0),
        st.floats(min_value=0.1, max_value=10.0),
    )
    def test_scale_invariance(self, total_ae, dose, factor):
        assume(total_ae * factor <= 500.0 and dose * factor <= 5000.0)
        r1 = percent_excreted(total_ae, dose)
        r2 = percent_excreted(total_ae * factor, dose * factor)
        assert np.isclose(r1, r2, rtol=1e-10)


class TestLambdaZ:
    @given(
        st.lists(st.floats(min_value=0.1, max_value=100.0), min_size=6, max_size=20),
    )
    def test_lambda_z_positive_for_declining_data(self, conc):
        conc = sorted(conc, reverse=True)
        assume(conc[0] > conc[-1])
        assume(len(set(conc)) >= 4)
        times = [float(i) for i in range(len(conc))]
        result = lambda_z(times, conc, method="auto")
        assert result.lambda_z > 0.0

    @given(
        st.lists(st.floats(min_value=0.1, max_value=100.0), min_size=6, max_size=20),
    )
    def test_half_life_equals_ln2_over_lambda_z(self, conc):
        conc = sorted(conc, reverse=True)
        assume(conc[0] > conc[-1])
        assume(len(set(conc)) >= 4)
        times = [float(i) for i in range(len(conc))]
        result = lambda_z(times, conc, method="auto")
        assert np.isclose(result.half_life, math.log(2) / result.lambda_z, rtol=1e-12)

    @given(
        st.lists(st.floats(min_value=0.1, max_value=100.0), min_size=8, max_size=15),
    )
    def test_n_points_matches_selected(self, conc):
        conc = sorted(conc, reverse=True)
        assume(conc[0] > conc[-1] * 2)
        assume(len(set(conc)) >= 4)
        times = [float(i) for i in range(len(conc))]
        result = lambda_z(times, conc, method="auto")
        assert result.n_points == len(result.selected_times)
        assert result.n_points == len(result.selected_concs)

    def test_manual_method_with_valid_range(self):
        times = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
        concs = [100.0, 80.0, 60.0, 40.0, 30.0, 20.0, 15.0, 10.0, 5.0]
        result = lambda_z(times, concs, method="manual", time_range=(4.0, 8.0))
        assert result.lambda_z > 0.0
        assert result.method == "manual"

    @given(
        st.lists(st.floats(min_value=0.1, max_value=100.0), min_size=6, max_size=15),
    )
    def test_auto_method_lambda_z_positive(self, conc):
        conc = sorted(conc, reverse=True)
        assume(conc[0] > conc[-1])
        assume(len(set(conc)) >= 4)
        times = [float(i) for i in range(len(conc))]
        result = lambda_z(times, conc, method="auto")
        assert result.lambda_z > 0.0
        assert result.method == "auto"
