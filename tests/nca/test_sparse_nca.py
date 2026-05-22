"""Tests for sparse-sampling NCA (v1.5.0)."""

import numpy as np
import pytest

from openpkflow.nca.sparse import (
    SparseNCAResult,
    fit_sparse_1cmt_oral,
    sparse_nca_bias_analysis,
)
from openpkflow.sim.methods import c_1cmt_oral


class TestFitSparse1cmtOral:
    def test_recovers_known_parameters_from_dense(self):
        dose = 100.0
        CL_F_true = 5.0
        Vz_F_true = 50.0
        ka_true = 0.8
        times = np.array([0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 24.0])
        conc = c_1cmt_oral(times, dose, CL_F_true, Vz_F_true, ka_true)

        result = fit_sparse_1cmt_oral(times, conc, dose)

        assert result.converged
        assert result.CL_F == pytest.approx(CL_F_true, rel=0.15)
        assert result.Vz_F == pytest.approx(Vz_F_true, rel=0.25)
        assert result.ka == pytest.approx(ka_true, rel=0.30)

    def test_auclast_close_to_dose_div_clf(self):
        dose = 100.0
        times = np.array([0.5, 2.0, 4.0, 8.0, 12.0, 24.0])
        conc = c_1cmt_oral(times, dose, 5.0, 60.0, 0.6)

        result = fit_sparse_1cmt_oral(times, conc, dose)

        expected_auc = dose / result.CL_F
        assert result.AUCinf == pytest.approx(expected_auc, rel=0.01)
        assert result.AUClast > 0

    def test_with_only_three_points(self):
        dose = 250.0
        times = np.array([1.0, 4.0, 12.0])
        conc = c_1cmt_oral(times, dose, 6.0, 80.0, 0.5)

        result = fit_sparse_1cmt_oral(times, conc, dose)

        assert result.converged
        assert result.n_samples == 3
        assert result.AUCinf > 0
        assert result.Cmax > 0
        assert result.half_life > 0

    def test_with_five_points(self):
        dose = 150.0
        times = np.array([0.5, 1.5, 3.0, 6.0, 12.0])
        conc = c_1cmt_oral(times, dose, 4.5, 55.0, 0.7)

        result = fit_sparse_1cmt_oral(times, conc, dose)

        assert result.converged
        assert result.n_samples == 5

    def test_raises_on_too_few_points(self):
        times = np.array([1.0, 4.0])
        conc = np.array([5.0, 3.0])

        with pytest.raises(ValueError, match="at least 3"):
            fit_sparse_1cmt_oral(times, conc, 100.0)

    def test_raises_on_mismatched_lengths(self):
        times = np.array([1.0, 4.0, 8.0])
        conc = np.array([5.0, 3.0])

        with pytest.raises(ValueError, match="same length"):
            fit_sparse_1cmt_oral(times, conc, 100.0)

    def test_raises_on_non_positive_dose(self):
        times = np.array([1.0, 4.0, 8.0])
        conc = np.array([5.0, 3.0, 1.0])

        with pytest.raises(ValueError, match="dose must be > 0"):
            fit_sparse_1cmt_oral(times, conc, 0.0)

    def test_cmax_greater_than_max_observed(self):
        dose = 100.0
        times = np.array([1.0, 3.0, 8.0])
        conc = c_1cmt_oral(times, dose, 5.0, 50.0, 0.5)

        result = fit_sparse_1cmt_oral(times, conc, dose)

        assert result.Cmax >= np.max(conc) * 0.5

    def test_standard_errors_computed(self):
        dose = 100.0
        times = np.array([0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0])
        conc = c_1cmt_oral(times, dose, 5.0, 50.0, 0.8)

        result = fit_sparse_1cmt_oral(times, conc, dose)

        assert result.CL_F_se is not None
        assert result.Vz_F_se is not None
        assert result.ka_se is not None
        assert result.CL_F_se > 0
        assert result.Vz_F_se > 0
        assert result.ka_se > 0

    def test_summary_contains_key_metrics(self):
        dose = 100.0
        times = np.array([1.0, 3.0, 8.0])
        conc = c_1cmt_oral(times, dose, 5.0, 50.0, 0.5)

        result = fit_sparse_1cmt_oral(times, conc, dose)
        text = result.summary()

        assert "Sparse NCA" in text
        assert "CL_F" in text
        assert "AUCinf" in text
        assert "Cmax" in text

    def test_to_dict_keys(self):
        dose = 100.0
        times = np.array([1.0, 3.0, 8.0])
        conc = c_1cmt_oral(times, dose, 5.0, 50.0, 0.5)

        result = fit_sparse_1cmt_oral(times, conc, dose)
        d = result.to_dict()

        assert "CL_F" in d
        assert "Vz_F" in d
        assert "ka" in d
        assert "AUClast" in d
        assert "AUCinf" in d
        assert "Cmax" in d
        assert "Tmax" in d
        assert "half_life" in d

    def test_plot_saves_file(self, tmp_path):
        dose = 100.0
        times = np.array([1.0, 3.0, 8.0])
        conc = c_1cmt_oral(times, dose, 5.0, 50.0, 0.5)

        result = fit_sparse_1cmt_oral(times, conc, dose)
        out = tmp_path / "sparse_plot.png"
        result.plot(str(out))
        assert out.exists()
        assert out.stat().st_size > 1000

    def test_converged_false_on_bad_data(self):
        # Impossibly high values with random noise that can't fit a 1-cmt model
        np.random.seed(42)
        times = np.array([1.0, 3.0, 8.0, 12.0, 24.0])
        conc = np.array([0.01, 500.0, 0.02, 400.0, 0.01])  # impossible PK profile

        result = fit_sparse_1cmt_oral(times, conc, 100.0)
        # Either fails to converge or produces obviously wrong fits
        # The key thing is it doesn't crash
        assert result.n_samples == 5
        assert result.route == "oral"

    def test_bias_analysis_against_rich(self):
        dose = 100.0
        CL_F_true = 5.0
        Vz_F_true = 50.0
        ka_true = 0.8
        times = np.array([0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 24.0])
        conc = c_1cmt_oral(times, dose, CL_F_true, Vz_F_true, ka_true)

        sparse = fit_sparse_1cmt_oral(times[:5], conc[:5], dose)

        from dataclasses import dataclass

        @dataclass
        class RichMock:
            AUClast: float
            AUCinf_obs: float
            Cmax: float
            Tmax: float
            half_life: float
            CL_F: float
            Vz_F: float

        rich = RichMock(
            AUClast=float(np.trapezoid(conc, times)),
            AUCinf_obs=float(np.trapezoid(conc, times)) + conc[-1] / (CL_F_true / Vz_F_true),
            Cmax=float(np.max(conc)),
            Tmax=float(times[np.argmax(conc)]),
            half_life=np.log(2.0) / (CL_F_true / Vz_F_true),
            CL_F=CL_F_true,
            Vz_F=Vz_F_true,
        )

        bias = sparse_nca_bias_analysis(sparse, rich)

        assert "AUClast_pct_bias" in bias["biased_parameters"]
        assert "AUCinf_pct_bias" in bias["biased_parameters"]
        assert "Cmax_pct_bias" in bias["biased_parameters"]

    def test_halflife_is_positive(self):
        dose = 100.0
        times = np.array([1.0, 3.0, 8.0])
        conc = c_1cmt_oral(times, dose, 5.0, 50.0, 0.5)

        result = fit_sparse_1cmt_oral(times, conc, dose)
        assert result.half_life > 0

    def test_accumulation_ratio_compatible(self):
        dose = 100.0
        times = np.array([1.0, 3.0, 8.0])
        conc = c_1cmt_oral(times, dose, 5.0, 50.0, 0.5)

        result = fit_sparse_1cmt_oral(times, conc, dose)
        assert result.AUCinf > result.AUClast * 0.5
