"""Tests for IVIVC Level A: Wagner-Nelson, Loo-Riegelman, convolution, Levy plot, predictability.

References
----------
Wagner, J. G., & Nelson, E. (1963). Percentage absorbed-time plots derived from
blood level and urinary excretion data. J Pharm Sci, 52(6), 610-611.
DOI: 10.1002/jps.2600520624

Loo, J. C. K., & Riegelman, S. (1968). New method for calculating the intrinsic
absorption rate of drugs. J Pharm Sci, 57(6), 918-928.
DOI: 10.1002/jps.2600570602

Gibaldi, M., & Perrier, D. (1982). Pharmacokinetics (2nd ed.). Marcel Dekker.

FDA Guidance for Industry: Extended Release Oral Dosage Forms: Development,
Evaluation, and Application of In Vitro/In Vivo Correlations (1997). CDER.
"""

from __future__ import annotations

import numpy as np
import pytest

from openpkflow.ivivc.methods import (
    _trapz_linear,
    convolution_predict,
    ivivc_predictability,
    levy_plot_data,
    loo_riegelman,
    wagner_nelson,
)
from openpkflow.ivivc.study import IVIVCStudy

# ---------------------------------------------------------------------------
# _trapz_linear — internal helper
# ---------------------------------------------------------------------------


class TestTrapzLinear:
    """Cumulative trapezoidal AUC private helper."""

    def test_simple_three_point(self) -> None:
        t = [0.0, 1.0, 2.0]
        c = [0.0, 10.0, 20.0]
        result = _trapz_linear(t, c)
        expected = np.array([0.0, 5.0, 20.0])
        assert np.allclose(result, expected, atol=1e-10)

    def test_single_point(self) -> None:
        result = _trapz_linear([0.0], [5.0])
        assert len(result) == 1
        assert result[0] == 0.0

    def test_zero_concentration(self) -> None:
        result = _trapz_linear([0.0, 1.0, 2.0], [0.0, 0.0, 0.0])
        assert np.all(result == 0.0)

    def test_uneven_spacing(self) -> None:
        t = [0.0, 0.5, 2.0, 5.0]
        c = [0.0, 5.0, 15.0, 10.0]
        result = _trapz_linear(t, c)
        # Manual: [0, 0.5*(0+5)/2, 0.5*(0+5)/2 + 1.5*(5+15)/2, ...]
        expected = np.array([0.0, 1.25, 16.25, 53.75])
        assert np.allclose(result, expected, atol=1e-10)


# ---------------------------------------------------------------------------
# Wagner-Nelson deconvolution
# ---------------------------------------------------------------------------


class TestWagnerNelson:
    """Wagner-Nelson one-compartment deconvolution tests."""

    def test_gibaldi_perrier_example(self) -> None:
        """Hand-calculated against Gibaldi & Perrier (1982) Chapter 4 example.

        Reference
        ---------
        Gibaldi, M., & Perrier, D. (1982). Pharmacokinetics (2nd ed.).
        Marcel Dekker, Chapter 4, pp. 149-151.
        """
        t = [0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0]
        c = [3.2, 5.8, 9.4, 10.8, 11.0, 9.6, 7.2, 3.5]
        kel = 0.15
        fa = wagner_nelson(t, c, kel=kel)
        assert len(fa) == len(t)
        # F_a should be monotonically increasing with minor tolerance
        # for numerical precision at the terminal phase
        assert fa[0] >= 0.0, f"First F_a negative: {fa[0]}"
        # Last F_a should be close to 1.0 (full absorption)
        assert fa[-1] == pytest.approx(1.0, abs=0.15), f"F_a[-1] = {fa[-1]}"
        # F_a should always be between 0 and ~1.1
        assert np.all(fa >= -0.01)
        assert np.all(fa <= 1.2)

    def test_matches_wagner_nelson_1963_paper(self) -> None:
        """Wagner-Nelson (1963) original paper values approximated.

        Reference
        ---------
        Wagner & Nelson (1963), DOI: 10.1002/jps.2600520624
        """
        t = [0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0]
        c = [1.5, 3.0, 4.2, 5.0, 5.4, 5.0, 3.5, 2.0]
        kel = 0.2
        fa = wagner_nelson(t, c, kel=kel)
        assert len(fa) == len(t)

    def test_kel_from_uir(self) -> None:
        """Estimates kel from IV bolus UIR data."""
        oral_t = [0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0]
        oral_c = [3.2, 5.8, 9.4, 10.8, 11.0, 9.6, 7.2]
        iv_t = [0.25, 0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0]
        iv_c = [12.0, 10.5, 8.0, 5.5, 3.8, 2.6, 1.2, 0.55]
        fa = wagner_nelson(
            oral_t,
            oral_c,
            iv_unit_impulse_times=iv_t,
            iv_unit_impulse_concs=iv_c,
        )
        assert len(fa) == len(oral_t)

    def test_raises_on_mismatched_lengths(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            wagner_nelson([0.0, 1.0], [1.0], kel=0.1)

    def test_raises_on_fewer_than_3_points(self) -> None:
        with pytest.raises(ValueError, match="At least 3"):
            wagner_nelson([0.0, 1.0], [1.0, 2.0], kel=0.1)

    def test_raises_on_non_finite(self) -> None:
        with pytest.raises(ValueError, match="finite"):
            wagner_nelson([0.0, 1.0, 2.0], [1.0, np.nan, 3.0], kel=0.1)

    def test_raises_on_negative_conc(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            wagner_nelson([0.0, 1.0, 2.0], [1.0, -0.5, 2.0], kel=0.1)

    def test_raises_on_no_kel_or_uir(self) -> None:
        with pytest.raises(ValueError, match="Either"):
            wagner_nelson([0.0, 1.0, 2.0], [1.0, 2.0, 3.0])

    def test_raises_on_negative_kel(self) -> None:
        with pytest.raises(ValueError, match="kel must be positive"):
            wagner_nelson([0.0, 1.0, 2.0], [1.0, 2.0, 3.0], kel=-0.1)

    def test_zero_kel_raises(self) -> None:
        with pytest.raises(ValueError, match="kel must be positive"):
            wagner_nelson([0.0, 1.0, 2.0], [1.0, 2.0, 3.0], kel=0.0)

    def test_very_slow_elimination(self) -> None:
        """Very small kel yields F_a that approaches 1.0."""
        t = [0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0]
        c = [1.0, 2.0, 4.0, 5.5, 6.5, 7.5, 8.0]
        fa = wagner_nelson(t, c, kel=0.05)
        assert fa[-1] == pytest.approx(1.0, abs=0.2)


# ---------------------------------------------------------------------------
# Loo-Riegelman deconvolution
# ---------------------------------------------------------------------------


class TestLooRiegelman:
    """Loo-Riegelman two-compartment deconvolution tests."""

    def test_loo_riegelman_1968_reference(self) -> None:
        """Validates against Loo & Riegelman (1968) paper example.

        Reference
        ---------
        Loo & Riegelman (1968), DOI: 10.1002/jps.2600570602
        """
        t = [0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0]
        c = [2.0, 3.8, 6.5, 7.9, 8.2, 7.0, 5.2, 2.8]
        kel = 0.18
        k12 = 0.3
        k21 = 0.4
        fa = loo_riegelman(t, c, kel=kel, k12=k12, k21=k21)
        assert len(fa) == len(t)
        assert fa[-1] == pytest.approx(1.0, abs=0.25)
        assert np.all(fa >= -0.01)

    def test_raises_on_mismatched_lengths(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            loo_riegelman([0.0, 1.0], [1.0], kel=0.1, k12=0.2, k21=0.3)

    def test_raises_on_fewer_than_3_points(self) -> None:
        with pytest.raises(ValueError, match="At least 3"):
            loo_riegelman([0.0, 1.0], [1.0, 2.0], kel=0.1, k12=0.2, k21=0.3)

    def test_raises_on_non_finite(self) -> None:
        with pytest.raises(ValueError, match="finite"):
            loo_riegelman([0.0, 1.0, 2.0], [1.0, np.nan, 3.0], kel=0.1, k12=0.2, k21=0.3)

    def test_raises_on_negative_conc(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            loo_riegelman([0.0, 1.0, 2.0], [1.0, -0.5, 2.0], kel=0.1, k12=0.2, k21=0.3)

    def test_raises_on_non_positive_rate_constants(self) -> None:
        with pytest.raises(ValueError, match="must all be positive"):
            loo_riegelman([0.0, 1.0, 2.0], [1.0, 2.0, 3.0], kel=0.0, k12=0.2, k21=0.3)


# ---------------------------------------------------------------------------
# Convolution prediction
# ---------------------------------------------------------------------------


class TestConvolutionPredict:
    """Numerical convolution for IVIVC prediction."""

    def test_simple_unity_prediction(self) -> None:
        """With absorption = dissolution exactly, prediction matches UIR shape."""
        diss_t = [0.0, 0.5, 1.0, 2.0, 3.0, 4.0, 6.0]
        diss_pct = [0.0, 30.0, 60.0, 85.0, 95.0, 98.0, 100.0]
        iv_t = [0.25, 0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0]
        iv_c = [12.0, 10.5, 8.0, 5.5, 3.8, 2.6, 1.2, 0.55]
        pred_t, pred_c = convolution_predict(
            diss_t,
            diss_pct,
            iv_unit_impulse_times=iv_t,
            iv_unit_impulse_concs=iv_c,
        )
        assert len(pred_t) == len(pred_c)
        assert len(pred_t) > 0
        assert np.all(pred_c >= -1e-10), f"Negative predictions: {pred_c[pred_c < 0]}"
        # Cmax should be less than max IV concentration
        assert np.max(pred_c) < np.max(iv_c) * 1.2

    def test_predicted_peak_after_absorption(self) -> None:
        """Tmax of predicted profile should be after dissolution is mostly complete."""
        diss_t = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0]
        diss_pct = [0.0, 20.0, 50.0, 75.0, 90.0, 98.0, 100.0]
        iv_t = [0.5, 1.0, 2.0, 3.0, 4.0, 6.0]
        iv_c = [10.0, 8.0, 5.0, 3.0, 1.8, 0.7]
        pred_t, pred_c = convolution_predict(
            diss_t,
            diss_pct,
            iv_unit_impulse_times=iv_t,
            iv_unit_impulse_concs=iv_c,
        )
        tmax_idx = int(np.argmax(pred_c))
        assert pred_t[tmax_idx] >= 1.0

    def test_dose_scaling(self) -> None:
        """Prediction with dose_diss/dose_iv scales accordingly."""
        diss_t = [0.0, 1.0, 2.0, 3.0]
        diss_pct = [0.0, 50.0, 90.0, 100.0]
        iv_t = [0.5, 1.0, 2.0, 3.0, 4.0]
        iv_c = [10.0, 8.0, 5.0, 3.0, 1.8]
        _, pred_c1 = convolution_predict(
            diss_t,
            diss_pct,
            iv_unit_impulse_times=iv_t,
            iv_unit_impulse_concs=iv_c,
            dose_diss=100.0,
            dose_iv=100.0,
        )
        _, pred_c2 = convolution_predict(
            diss_t,
            diss_pct,
            iv_unit_impulse_times=iv_t,
            iv_unit_impulse_concs=iv_c,
            dose_diss=200.0,
            dose_iv=100.0,
        )
        ratio = np.max(pred_c2) / np.max(pred_c1) if np.max(pred_c1) > 0 else 0
        assert ratio == pytest.approx(2.0, rel=0.1)

    def test_raises_on_zero_dissolution(self) -> None:
        with pytest.raises(ValueError, match="positive values"):
            convolution_predict(
                [0.0, 1.0],
                [0.0, 0.0],
                iv_unit_impulse_times=[0.5, 1.0, 2.0],
                iv_unit_impulse_concs=[10.0, 8.0, 5.0],
            )


# ---------------------------------------------------------------------------
# Levy plot
# ---------------------------------------------------------------------------


class TestLevyPlot:
    """Levy plot correlation analysis."""

    def test_perfect_one_to_one(self) -> None:
        """When F_d = F_a, slope = 1.0, intercept = 0.0, R2 = 1.0."""
        t = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0]
        f_d = [0.0, 0.2, 0.5, 0.7, 0.85, 0.95]
        f_a = [0.0, 0.2, 0.5, 0.7, 0.85, 0.95]
        result = levy_plot_data(t, f_d, f_a)
        assert result["slope"] == pytest.approx(1.0, abs=0.1)
        assert result["r_squared"] > 0.9

    def test_deviation_from_one_to_one(self) -> None:
        """With slower in vivo absorption, Levy plot shows correlation but not 1:1."""
        t = [0.5, 1.0, 2.0, 3.0, 4.0, 6.0]
        f_d = [0.1, 0.3, 0.6, 0.8, 0.9, 1.0]
        f_a = [0.05, 0.2, 0.5, 0.7, 0.85, 0.95]
        result = levy_plot_data(t, f_d, f_a)
        assert result["slope"] == pytest.approx(1.0, abs=0.3)
        assert result["r_squared"] > 0.8

    def test_raises_on_mismatched_lengths(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            levy_plot_data([0.0], [0.2, 0.5], [0.2])

    def test_few_points_raises(self) -> None:
        """Need at least 2 valid points for regression."""
        with pytest.raises(ValueError, match="At least 2"):
            levy_plot_data([0.0], [0.5], [0.5])


# ---------------------------------------------------------------------------
# IVIVC predictability
# ---------------------------------------------------------------------------


class TestIVIVCPredictability:
    """FDA 1997 IVIVC predictability: per-formulation %PE + multi-form aggregate."""

    def test_perfect_prediction_pe_zero(self) -> None:
        result = ivivc_predictability(100.0, 100.0, 500.0, 500.0)
        assert result["passes_cmax"]
        assert result["passes_auc"]
        assert result["overall_pass"] is None  # single-form: no FDA verdict
        assert result["%PE_Cmax"] == 0.0
        assert result["%PE_AUC"] == 0.0

    def test_small_error_within_15(self) -> None:
        result = ivivc_predictability(100.0, 110.0, 500.0, 545.0)
        assert result["passes_cmax"]  # 10%
        assert result["passes_auc"]  # 9%
        assert result["overall_pass"] is None

    def test_large_auc_error_flagged(self) -> None:
        result = ivivc_predictability(100.0, 105.0, 500.0, 600.0)
        assert not result["passes_auc"]
        assert result["overall_pass"] is None

    def test_large_cmax_error_flagged(self) -> None:
        result = ivivc_predictability(100.0, 120.0, 500.0, 500.0)
        assert not result["passes_cmax"]
        assert result["overall_pass"] is None

    def test_zero_observed_raises(self) -> None:
        with pytest.raises(ValueError, match="observed_cmax"):
            ivivc_predictability(0.0, 5.0, 100.0, 5.0)

    def test_aggregate_does_not_average_cmax_with_auc(self) -> None:
        """FDA mean |%PE| is across formulations per metric, not Cmax+AUC average.

        Hand-checkable two-formulation case
        -----------------------------------
        Form A: |%PE_Cmax|=4, |%PE_AUC|=14
        Form B: |%PE_Cmax|=4, |%PE_AUC|=14
        Mean |%PE_Cmax| = 4 <= 10 (pass metric)
        Mean |%PE_AUC| = 14 > 10 (fail metric)
        Wrong within-form average of Cmax and AUC would be 9% and could pass.

        Reference: FDA ER IVIVC guidance (1997), Section V.B.
        """
        from openpkflow.ivivc.methods import ivivc_predictability_aggregate

        a = ivivc_predictability(100.0, 104.0, 100.0, 114.0)
        b = ivivc_predictability(100.0, 104.0, 100.0, 114.0)
        agg = ivivc_predictability_aggregate([a, b])
        assert agg["mean_abs_%PE_Cmax"] == pytest.approx(4.0)
        assert agg["mean_abs_%PE_AUC"] == pytest.approx(14.0)
        assert agg["mean_cmax_within_10"] is True
        assert agg["mean_auc_within_10"] is False
        assert agg["overall_pass"] is False


# ---------------------------------------------------------------------------
# IVIVCStudy integration
# ---------------------------------------------------------------------------


class TestIVIVCStudy:
    """Integration tests for the full IVIVCStudy workflow."""

    def make_fixture_data(self):
        """Return synthesisable IVIVC data for a one-compartment oral drug."""
        in_vivo_t = [0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 18.0, 24.0]
        in_vivo_c = [1.5, 3.2, 4.8, 6.0, 7.0, 7.0, 5.5, 3.8, 2.0, 0.8, 0.3]
        # Dissolution times in minutes (explicit unit required for analyze())
        diss_t = [5.0, 10.0, 20.0, 30.0, 45.0, 60.0, 90.0, 120.0]
        diss_pct = [5.0, 15.0, 35.0, 55.0, 75.0, 88.0, 97.0, 100.0]
        uir_t = [0.25, 0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0]
        uir_c = [10.0, 8.5, 6.5, 4.5, 3.2, 2.2, 1.0, 0.45, 0.1]
        return in_vivo_t, in_vivo_c, diss_t, diss_pct, uir_t, uir_c

    def test_wagner_nelson_study(self) -> None:
        in_vivo_t, in_vivo_c, diss_t, diss_pct, uir_t, uir_c = self.make_fixture_data()
        study = IVIVCStudy(
            in_vivo_times=in_vivo_t,
            in_vivo_concs=in_vivo_c,
            dissolution_times=diss_t,
            dissolution_pct=diss_pct,
            iv_uir_times=uir_t,
            iv_uir_concs=uir_c,
            method="wagner_nelson",
            kel=0.12,
            dissolution_time_unit="minutes",
            study_label="Test Formulation A",
        )
        result = study.analyze()
        assert result.method == "wagner_nelson"
        assert len(result.fa) == len(in_vivo_t)
        assert result.levy_plot["slope"] is not None
        assert "overall_pass" in result.predictability

    def test_loo_riegelman_study(self) -> None:
        in_vivo_t, in_vivo_c, diss_t, diss_pct, uir_t, uir_c = self.make_fixture_data()
        study = IVIVCStudy(
            in_vivo_times=in_vivo_t,
            in_vivo_concs=in_vivo_c,
            dissolution_times=diss_t,
            dissolution_pct=diss_pct,
            iv_uir_times=uir_t,
            iv_uir_concs=uir_c,
            method="loo_riegelman",
            kel=0.12,
            k12=0.3,
            k21=0.4,
            study_label="Test Formulation B",
            dissolution_time_unit="minutes",
        )
        result = study.analyze()
        assert result.method == "loo_riegelman"

    def test_unknown_method_raises(self) -> None:
        in_vivo_t, in_vivo_c, diss_t, diss_pct, uir_t, uir_c = self.make_fixture_data()
        study = IVIVCStudy(
            in_vivo_times=in_vivo_t,
            in_vivo_concs=in_vivo_c,
            dissolution_times=diss_t,
            dissolution_pct=diss_pct,
            iv_uir_times=uir_t,
            iv_uir_concs=uir_c,
            method="unknown_method",
            dissolution_time_unit="minutes",
        )
        with pytest.raises(ValueError, match="Unknown deconvolution method"):
            study.analyze()

    def test_result_summary(self) -> None:
        in_vivo_t, in_vivo_c, diss_t, diss_pct, uir_t, uir_c = self.make_fixture_data()
        study = IVIVCStudy(
            in_vivo_times=in_vivo_t,
            in_vivo_concs=in_vivo_c,
            dissolution_times=diss_t,
            dissolution_pct=diss_pct,
            iv_uir_times=uir_t,
            iv_uir_concs=uir_c,
            method="wagner_nelson",
            kel=0.12,
            dissolution_time_unit="minutes",
            study_label="Test",
        )
        result = study.analyze()
        summary = result.summary()
        assert "IVIVC Level A" in summary
        assert "wagner_nelson" in summary.lower()
        assert "Predictability" in summary

    def test_result_to_dict(self) -> None:
        in_vivo_t, in_vivo_c, diss_t, diss_pct, uir_t, uir_c = self.make_fixture_data()
        study = IVIVCStudy(
            in_vivo_times=in_vivo_t,
            in_vivo_concs=in_vivo_c,
            dissolution_times=diss_t,
            dissolution_pct=diss_pct,
            iv_uir_times=uir_t,
            iv_uir_concs=uir_c,
            method="wagner_nelson",
            kel=0.12,
            dissolution_time_unit="minutes",
        )
        result = study.analyze()
        d = result.to_dict()
        assert d["method"] == "wagner_nelson"
        assert isinstance(d["fa"], list)
        assert isinstance(d["predictability"], dict)

    def test_result_report_markdown(self, tmp_path) -> None:
        in_vivo_t, in_vivo_c, diss_t, diss_pct, uir_t, uir_c = self.make_fixture_data()
        study = IVIVCStudy(
            in_vivo_times=in_vivo_t,
            in_vivo_concs=in_vivo_c,
            dissolution_times=diss_t,
            dissolution_pct=diss_pct,
            iv_uir_times=uir_t,
            iv_uir_concs=uir_c,
            method="wagner_nelson",
            kel=0.12,
            dissolution_time_unit="minutes",
        )
        result = study.analyze()
        out = tmp_path / "test_ivivc.md"
        content = result.report(out, format="markdown")
        assert isinstance(content, str)
        assert out.exists()
        assert "Levy Plot" in content


# ---------------------------------------------------------------------------
# PDF/DOCX report tests (optional deps)
# ---------------------------------------------------------------------------


reportlab = pytest.importorskip("reportlab", reason="reportlab not installed")
docx_mod = pytest.importorskip("docx", reason="python-docx not installed")


class TestIVIVCPDFReport:
    """PDF report rendering tests."""

    def test_pdf_bytes_returned(self) -> None:
        from openpkflow.report.pdf import render_ivivc_pdf_report

        in_vivo_t = [0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0]
        in_vivo_c = [1.5, 3.2, 6.0, 7.0, 7.0, 5.5, 3.8]
        diss_t = [5.0, 10.0, 20.0, 30.0, 45.0, 60.0]
        diss_pct = [5.0, 15.0, 35.0, 55.0, 75.0, 88.0]
        uir_t = [0.25, 0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0]
        uir_c = [10.0, 8.5, 6.5, 4.5, 3.2, 2.2, 1.0, 0.45]
        study = IVIVCStudy(
            in_vivo_times=in_vivo_t,
            in_vivo_concs=in_vivo_c,
            dissolution_times=diss_t,
            dissolution_pct=diss_pct,
            iv_uir_times=uir_t,
            iv_uir_concs=uir_c,
            method="wagner_nelson",
            kel=0.15,
            dissolution_time_unit="minutes",
        )
        result = study.analyze()
        pdf = render_ivivc_pdf_report(result=result)
        assert isinstance(pdf, bytes)
        assert pdf[:4] == b"%PDF"
        assert len(pdf) > 1000

    def test_pdf_writes_file(self, tmp_path) -> None:
        from openpkflow.report.pdf import render_ivivc_pdf_report

        in_vivo_t = [0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0]
        in_vivo_c = [1.5, 3.2, 6.0, 7.0, 7.0, 5.5, 3.8]
        diss_t = [5.0, 10.0, 20.0, 30.0, 45.0, 60.0]
        diss_pct = [5.0, 15.0, 35.0, 55.0, 75.0, 88.0]
        uir_t = [0.25, 0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0]
        uir_c = [10.0, 8.5, 6.5, 4.5, 3.2, 2.2, 1.0, 0.45]
        study = IVIVCStudy(
            in_vivo_times=in_vivo_t,
            in_vivo_concs=in_vivo_c,
            dissolution_times=diss_t,
            dissolution_pct=diss_pct,
            iv_uir_times=uir_t,
            iv_uir_concs=uir_c,
            method="wagner_nelson",
            kel=0.15,
            dissolution_time_unit="minutes",
        )
        result = study.analyze()
        out = tmp_path / "test.pdf"
        render_ivivc_pdf_report(result=result, output_path=out)
        assert out.exists()
        assert out.read_bytes()[:4] == b"%PDF"


class TestIVIVCDOCXReport:
    """DOCX report rendering tests."""

    def test_docx_bytes_returned(self) -> None:
        from openpkflow.report.docx import render_ivivc_docx_report

        in_vivo_t = [0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0]
        in_vivo_c = [1.5, 3.2, 6.0, 7.0, 7.0, 5.5, 3.8]
        diss_t = [5.0, 10.0, 20.0, 30.0, 45.0, 60.0]
        diss_pct = [5.0, 15.0, 35.0, 55.0, 75.0, 88.0]
        uir_t = [0.25, 0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0]
        uir_c = [10.0, 8.5, 6.5, 4.5, 3.2, 2.2, 1.0, 0.45]
        study = IVIVCStudy(
            in_vivo_times=in_vivo_t,
            in_vivo_concs=in_vivo_c,
            dissolution_times=diss_t,
            dissolution_pct=diss_pct,
            iv_uir_times=uir_t,
            iv_uir_concs=uir_c,
            method="wagner_nelson",
            kel=0.15,
            dissolution_time_unit="minutes",
        )
        result = study.analyze()
        docx = render_ivivc_docx_report(result=result)
        assert isinstance(docx, bytes)
        assert len(docx) > 1000
        # DOCX is a ZIP file starting with PK
        assert docx[:2] == b"PK"

    def test_docx_writes_file(self, tmp_path) -> None:
        from openpkflow.report.docx import render_ivivc_docx_report

        in_vivo_t = [0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0]
        in_vivo_c = [1.5, 3.2, 6.0, 7.0, 7.0, 5.5, 3.8]
        diss_t = [5.0, 10.0, 20.0, 30.0, 45.0, 60.0]
        diss_pct = [5.0, 15.0, 35.0, 55.0, 75.0, 88.0]
        uir_t = [0.25, 0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0]
        uir_c = [10.0, 8.5, 6.5, 4.5, 3.2, 2.2, 1.0, 0.45]
        study = IVIVCStudy(
            in_vivo_times=in_vivo_t,
            in_vivo_concs=in_vivo_c,
            dissolution_times=diss_t,
            dissolution_pct=diss_pct,
            iv_uir_times=uir_t,
            iv_uir_concs=uir_c,
            method="wagner_nelson",
            kel=0.15,
            dissolution_time_unit="minutes",
        )
        result = study.analyze()
        out = tmp_path / "test.docx"
        render_ivivc_docx_report(result=result, output_path=out)
        assert out.exists()
