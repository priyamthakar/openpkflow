"""Unit tests for openpkflow.nca.methods — pure NCA math functions.

Each test has either a hand-checkable degenerate case or a published reference value.
Reference: FDA Guidance for Industry: Bioavailability and Bioequivalence Studies
           for Orally Administered Drug Products (2003); Gibaldi & Perrier,
           Pharmacokinetics 2nd ed.
"""

from __future__ import annotations

import math

import pytest

from openpkflow.nca.methods import (
    AUCResult,
    LambdaZResult,
    auc_inf_obs,
    auc_linear,
    auc_linear_up_log_down,
    auc_log,
    auc_percent_extrapolated,
    clearance_volume_parameters,
    cmax,
    lambda_z,
    tmax,
)

# ---------------------------------------------------------------------------
# auc_linear
# ---------------------------------------------------------------------------


class TestAucLinear:
    def test_flat_profile_two_points(self) -> None:
        # Trapezoid with equal heights: area = height * width = 10 * 1 = 10
        assert auc_linear([0.0, 1.0], [10.0, 10.0]) == pytest.approx(10.0)

    def test_triangle_two_intervals(self) -> None:
        # (0,0)→(1,2)→(2,0): two triangles each of area 1 → total 2
        assert auc_linear([0.0, 1.0, 2.0], [0.0, 2.0, 0.0]) == pytest.approx(2.0)

    def test_three_intervals(self) -> None:
        # Uniform trapezoids: c=[0,4,4,0], t=[0,1,2,3]
        # (0+4)/2*1 + (4+4)/2*1 + (4+0)/2*1 = 2 + 4 + 2 = 8
        assert auc_linear([0.0, 1.0, 2.0, 3.0], [0.0, 4.0, 4.0, 0.0]) == pytest.approx(8.0)

    def test_returns_float(self) -> None:
        result = auc_linear([0.0, 1.0], [5.0, 3.0])
        assert isinstance(result, float)

    def test_raises_on_length_mismatch(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            auc_linear([0.0, 1.0], [1.0, 2.0, 3.0])

    def test_raises_on_fewer_than_two_points(self) -> None:
        with pytest.raises(ValueError, match="At least 2"):
            auc_linear([0.0], [5.0])

    def test_raises_on_non_increasing_times(self) -> None:
        with pytest.raises(ValueError, match="strictly increasing"):
            auc_linear([0.0, 1.0, 1.0], [1.0, 2.0, 3.0])

    def test_raises_on_negative_concentration(self) -> None:
        with pytest.raises(ValueError, match="negative"):
            auc_linear([0.0, 1.0], [5.0, -1.0])


# ---------------------------------------------------------------------------
# auc_log
# ---------------------------------------------------------------------------


class TestAucLog:
    def test_returns_auc_result(self) -> None:
        result = auc_log([0.0, 1.0], [10.0, 5.0])
        assert isinstance(result, AUCResult)

    def test_declining_interval_log_mean(self) -> None:
        # Interval [0,1]: c0=10, c1=5 (declining)
        # Log mean concentration = (10-5)/ln(10/5) = 5/ln2 ≈ 7.2135
        # AUC = 7.2135 * 1 ≈ 7.2135
        result = auc_log([0.0, 1.0], [10.0, 5.0])
        expected = 5.0 / math.log(10.0 / 5.0)
        assert result.value == pytest.approx(expected, rel=1e-6)
        assert result.warnings == []

    def test_equal_concentrations_fallback_to_linear(self) -> None:
        # c1 == c2: log rule invalid, falls back to linear, warning appended
        result = auc_log([0.0, 1.0], [5.0, 5.0])
        assert result.value == pytest.approx(5.0)
        assert len(result.warnings) == 1
        assert "fell back to linear" in result.warnings[0]

    def test_zero_concentration_fallback(self) -> None:
        result = auc_log([0.0, 1.0], [0.0, 5.0])
        assert result.value == pytest.approx(2.5)  # linear: (0+5)/2*1
        assert len(result.warnings) == 1

    def test_no_warnings_for_clean_declining_profile(self) -> None:
        result = auc_log([0.0, 1.0, 2.0], [8.0, 4.0, 2.0])
        assert result.warnings == []


# ---------------------------------------------------------------------------
# auc_linear_up_log_down
# ---------------------------------------------------------------------------


class TestAucLinearUpLogDown:
    def test_returns_auc_result(self) -> None:
        result = auc_linear_up_log_down([0.0, 1.0, 2.0], [2.0, 4.0, 2.0])
        assert isinstance(result, AUCResult)

    def test_rising_uses_linear(self) -> None:
        # Interval [0→1]: c rises 2→4, linear = (2+4)/2*1 = 3.0
        result = auc_linear_up_log_down([0.0, 1.0], [2.0, 4.0])
        assert result.value == pytest.approx(3.0)
        assert result.warnings == []

    def test_declining_uses_log(self) -> None:
        # Interval [1→2]: c declines 4→2, log = (4-2)/ln(4/2)*1 = 2/ln2 ≈ 2.8854
        result = auc_linear_up_log_down([1.0, 2.0], [4.0, 2.0])
        expected = 2.0 / math.log(4.0 / 2.0)
        assert result.value == pytest.approx(expected, rel=1e-6)

    def test_mixed_profile(self) -> None:
        # Rising [0→1]: linear (2+4)/2 = 3.0
        # Declining [1→2]: log 2/ln2 ≈ 2.885
        result = auc_linear_up_log_down([0.0, 1.0, 2.0], [2.0, 4.0, 2.0])
        expected = 3.0 + 2.0 / math.log(4.0 / 2.0)
        assert result.value == pytest.approx(expected, rel=1e-6)

    def test_flat_interval_treated_as_rising(self) -> None:
        # c2 == c1 (flat): treated as rising → linear
        result = auc_linear_up_log_down([0.0, 1.0], [5.0, 5.0])
        assert result.value == pytest.approx(5.0)
        assert result.warnings == []

    def test_declining_with_zero_fallback(self) -> None:
        result = auc_linear_up_log_down([0.0, 1.0], [4.0, 0.0])
        assert result.value == pytest.approx(2.0)  # linear: (4+0)/2*1
        assert len(result.warnings) == 1


# ---------------------------------------------------------------------------
# cmax
# ---------------------------------------------------------------------------


class TestCmax:
    def test_basic(self) -> None:
        assert cmax([3.0, 7.0, 5.0]) == pytest.approx(7.0)

    def test_nan_ignored(self) -> None:
        assert cmax([3.0, float("nan"), 7.0]) == pytest.approx(7.0)

    def test_single_element(self) -> None:
        assert cmax([4.2]) == pytest.approx(4.2)

    def test_raises_on_empty(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            cmax([])

    def test_raises_on_all_nan(self) -> None:
        with pytest.raises(ValueError, match="NaN"):
            cmax([float("nan"), float("nan")])


# ---------------------------------------------------------------------------
# tmax
# ---------------------------------------------------------------------------


class TestTmax:
    def test_basic(self) -> None:
        assert tmax([0.0, 1.0, 2.0], [3.0, 7.0, 5.0]) == pytest.approx(1.0)

    def test_first_occurrence_of_max(self) -> None:
        # Two equal maxima: tmax returns the first
        assert tmax([0.0, 1.0, 2.0], [7.0, 7.0, 3.0]) == pytest.approx(0.0)

    def test_raises_on_length_mismatch(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            tmax([0.0, 1.0], [1.0, 2.0, 3.0])

    def test_raises_on_empty(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            tmax([], [])

    def test_raises_on_all_nan(self) -> None:
        with pytest.raises(ValueError, match="NaN"):
            tmax([0.0, 1.0], [float("nan"), float("nan")])


# ---------------------------------------------------------------------------
# lambda_z (auto)
# ---------------------------------------------------------------------------


class TestLambdaZAuto:
    def _simple_declining(self) -> tuple[list[float], list[float]]:
        # Cmax at t=0; clean log-linear decline: c = 8 * exp(-0.5*t)
        times = [0.0, 1.0, 2.0, 3.0, 4.0]
        concs = [8.0, 4.0, 2.0, 1.0, 0.5]  # doubling time ~2h → lambda_z ≈ 0.693/2 ≈ 0.347
        return times, concs

    def test_returns_lambda_z_result(self) -> None:
        t, c = self._simple_declining()
        result = lambda_z(t, c)
        assert isinstance(result, LambdaZResult)

    def test_lambda_z_positive(self) -> None:
        t, c = self._simple_declining()
        result = lambda_z(t, c)
        assert result.lambda_z > 0.0

    def test_half_life_positive(self) -> None:
        t, c = self._simple_declining()
        result = lambda_z(t, c)
        assert result.half_life > 0.0

    def test_half_life_equals_ln2_over_lambda_z(self) -> None:
        t, c = self._simple_declining()
        result = lambda_z(t, c)
        assert result.half_life == pytest.approx(math.log(2) / result.lambda_z, rel=1e-9)

    def test_method_is_auto(self) -> None:
        t, c = self._simple_declining()
        result = lambda_z(t, c)
        assert result.method == "auto"

    def test_at_least_three_selected_points(self) -> None:
        t, c = self._simple_declining()
        result = lambda_z(t, c)
        assert result.n_points >= 3

    def test_raises_fewer_than_three_post_cmax(self) -> None:
        # Cmax at index 2; only 2 positive points after it
        with pytest.raises(ValueError, match="Fewer than 3"):
            lambda_z([0.0, 1.0, 2.0, 3.0, 4.0], [1.0, 2.0, 8.0, 4.0, 0.0])

    def test_r_squared_reasonable(self) -> None:
        t, c = self._simple_declining()
        result = lambda_z(t, c)
        assert result.r_squared > 0.99


class TestLambdaZManual:
    def test_time_range(self) -> None:
        times = [0.0, 1.0, 2.0, 3.0, 4.0]
        concs = [8.0, 4.0, 2.0, 1.0, 0.5]
        result = lambda_z(times, concs, method="manual", time_range=(1.0, 4.0))
        assert result.lambda_z > 0.0
        assert result.method == "manual"
        assert result.time_start == pytest.approx(1.0)

    def test_time_points(self) -> None:
        times = [0.0, 1.0, 2.0, 3.0, 4.0]
        concs = [8.0, 4.0, 2.0, 1.0, 0.5]
        result = lambda_z(times, concs, method="manual", time_points=[1.0, 2.0, 3.0, 4.0])
        assert result.lambda_z > 0.0
        assert result.n_points == 4

    def test_raises_both_specified(self) -> None:
        times = [0.0, 1.0, 2.0, 3.0]
        concs = [8.0, 4.0, 2.0, 1.0]
        with pytest.raises(ValueError, match="not both"):
            lambda_z(
                times,
                concs,
                method="manual",
                time_range=(1.0, 3.0),
                time_points=[1.0, 2.0, 3.0],
            )

    def test_raises_neither_specified(self) -> None:
        times = [0.0, 1.0, 2.0, 3.0]
        concs = [8.0, 4.0, 2.0, 1.0]
        with pytest.raises(ValueError, match="requires either"):
            lambda_z(times, concs, method="manual")

    def test_raises_unknown_time_point(self) -> None:
        times = [0.0, 1.0, 2.0, 3.0]
        concs = [8.0, 4.0, 2.0, 1.0]
        with pytest.raises(ValueError, match="not found"):
            lambda_z(times, concs, method="manual", time_points=[1.0, 99.0, 3.0])


# ---------------------------------------------------------------------------
# auc_inf_obs
# ---------------------------------------------------------------------------


class TestAucInfObs:
    def _mock_lz(self, lz_val: float) -> LambdaZResult:
        return LambdaZResult(
            lambda_z=lz_val,
            half_life=math.log(2) / lz_val,
            intercept=0.0,
            r_squared=0.99,
            adj_r_squared=0.99,
            n_points=3,
            time_start=1.0,
            time_end=4.0,
            selected_times=[1.0, 2.0, 4.0],
            selected_concs=[4.0, 2.0, 0.5],
            method="auto",
        )

    def test_basic(self) -> None:
        # AUClast=100, Clast=5, lambda_z=0.5 → 100 + 5/0.5 = 110
        lz = self._mock_lz(0.5)
        assert auc_inf_obs(100.0, 5.0, lz) == pytest.approx(110.0)

    def test_clast_zero(self) -> None:
        lz = self._mock_lz(0.5)
        assert auc_inf_obs(100.0, 0.0, lz) == pytest.approx(100.0)

    def test_raises_on_negative_clast(self) -> None:
        lz = self._mock_lz(0.5)
        with pytest.raises(ValueError, match=">= 0"):
            auc_inf_obs(100.0, -1.0, lz)


# ---------------------------------------------------------------------------
# auc_percent_extrapolated
# ---------------------------------------------------------------------------


class TestAucPercentExtrapolated:
    def test_ten_percent(self) -> None:
        # auclast=90, aucinf=100 → 10.0%
        assert auc_percent_extrapolated(90.0, 100.0) == pytest.approx(10.0)

    def test_zero_percent_when_equal(self) -> None:
        assert auc_percent_extrapolated(100.0, 100.0) == pytest.approx(0.0)

    def test_raises_on_non_positive_aucinf(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            auc_percent_extrapolated(50.0, 0.0)

    def test_raises_on_negative_aucinf(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            auc_percent_extrapolated(50.0, -10.0)


# ---------------------------------------------------------------------------
# clearance_volume_parameters
# ---------------------------------------------------------------------------


class TestClearanceVolumeParameters:
    def _mock_lz(self) -> LambdaZResult:
        return LambdaZResult(
            lambda_z=0.1,
            half_life=math.log(2) / 0.1,
            intercept=0.0,
            r_squared=0.99,
            adj_r_squared=0.99,
            n_points=4,
            time_start=1.0,
            time_end=10.0,
            selected_times=[1.0, 3.0, 6.0, 10.0],
            selected_concs=[4.0, 2.0, 1.0, 0.5],
            method="auto",
        )

    def test_oral_returns_clf_vzf(self) -> None:
        lz = self._mock_lz()
        params = clearance_volume_parameters(320.0, 100.0, lz, route="oral")
        assert "CL_F" in params
        assert "Vz_F" in params
        assert "CL" not in params
        assert "Vz" not in params

    def test_oral_values(self) -> None:
        # dose=320, aucinf=100, lambda_z=0.1
        # CL_F = 320/100 = 3.2; Vz_F = 320/(100*0.1) = 32
        lz = self._mock_lz()
        params = clearance_volume_parameters(320.0, 100.0, lz, route="oral")
        assert params["CL_F"] == pytest.approx(3.2)
        assert params["Vz_F"] == pytest.approx(32.0)

    def test_iv_bolus_returns_cl_vz(self) -> None:
        lz = self._mock_lz()
        params = clearance_volume_parameters(320.0, 100.0, lz, route="iv_bolus")
        assert "CL" in params
        assert "Vz" in params
        assert "CL_F" not in params
        assert "Vz_F" not in params

    def test_iv_infusion_returns_cl_vz(self) -> None:
        lz = self._mock_lz()
        params = clearance_volume_parameters(320.0, 100.0, lz, route="iv_infusion")
        assert "CL" in params

    def test_raises_on_invalid_route(self) -> None:
        lz = self._mock_lz()
        with pytest.raises(ValueError, match="route"):
            clearance_volume_parameters(320.0, 100.0, lz, route="subcutaneous")

    def test_raises_on_non_positive_aucinf(self) -> None:
        lz = self._mock_lz()
        with pytest.raises(ValueError, match="positive"):
            clearance_volume_parameters(320.0, 0.0, lz, route="oral")


# ---------------------------------------------------------------------------
# Edge-case tests: all-zero, NaN, trailing zero, degenerate profiles
# ---------------------------------------------------------------------------


class TestAucAllZero:
    """AUClast with all-zero concentrations must not crash and produce 0."""

    def test_linear_all_zero_is_zero(self) -> None:
        assert auc_linear([0, 1, 2], [0.0, 0.0, 0.0]) == 0.0

    def test_log_all_zero_is_zero(self) -> None:
        result = auc_log([0, 1, 2], [0.0, 0.0, 0.0])
        assert result.value == 0.0
        assert len(result.warnings) > 0  # every interval falls back

    def test_linear_up_log_down_all_zero_is_zero(self) -> None:
        result = auc_linear_up_log_down([0, 1, 2], [0.0, 0.0, 0.0])
        assert result.value == 0.0

    def test_linear_all_zero_single_point_raises(self) -> None:
        with pytest.raises(ValueError, match="2 points"):
            auc_linear([0], [0.0])


class TestAucAllNaN:
    """NaN concentrations should raise explicit errors, not silently propagate."""

    def test_linear_nan_raises(self) -> None:
        with pytest.raises(ValueError, match="negative|NaN"):
            auc_linear([0, 1, 2], [float("nan"), float("nan"), float("nan")])

    def test_log_nan_raises(self) -> None:
        with pytest.raises(ValueError, match="negative|NaN"):
            auc_log([0, 1, 2], [float("nan"), float("nan"), float("nan")])


class TestAucTrailingZero:
    """AUC functions should handle trailing zeros gracefully at the math level.
    The study-level tlast trimming is tested in test_study.py integration tests."""

    def test_linear_trailing_zero_included(self) -> None:
        v = auc_linear([0, 1, 2, 3], [5.0, 2.0, 0.5, 0.0])
        assert v > 0.0

    def test_linear_up_log_down_trailing_zero_included(self) -> None:
        result = auc_linear_up_log_down([0, 1, 2, 3], [5.0, 2.0, 0.5, 0.0])
        assert result.value > 0.0

    def test_log_trailing_zero_falls_back(self) -> None:
        result = auc_log([0, 1, 2, 3], [5.0, 2.0, 0.5, 0.0])
        assert result.value > 0.0
        assert len(result.warnings) >= 1  # trailing interval c2=0


class TestCmaxMixedWithZero:
    """Cmax should work when zeros and positives are interleaved."""

    def test_zero_in_middle(self) -> None:
        assert cmax([1.0, 0.0, 3.0, 0.0, 2.0]) == 3.0

    def test_all_zero(self) -> None:
        assert cmax([0.0, 0.0, 0.0]) == 0.0


class TestTmaxMixedWithZero:
    """Tmax should return time of first max including zeros."""

    def test_zero_is_max(self) -> None:
        assert tmax([0, 1, 2], [0.0, -0.5, -1.0]) == 0.0  # max is 0 at t=0
