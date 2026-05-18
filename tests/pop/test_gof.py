"""Tests for pop.gof module.

Reference: Bauer (2019) NONMEM Users Guide Part V for IWRES formulation.
Degenerate case: when DV == IPRED, IWRES == 0.
"""

import math

import numpy as np
import pytest

from openpkflow.pop.gof import GOFResult, compute_iwres, obs_pred_metrics


class TestComputeIwres:
    def test_degenerate_dv_equals_ipred(self):
        """IWRES must be 0 when DV == IPRED (by definition)."""
        dv = np.array([5.0, 10.0, 15.0])
        iwres = compute_iwres(dv, dv.copy(), sigma=1.0)
        np.testing.assert_allclose(iwres, 0.0, atol=1e-12)

    def test_proportional_formula(self):
        """IWRES = (DV - IPRED) / (sigma * IPRED)."""
        dv = np.array([12.0])
        ipred = np.array([10.0])
        sigma = 0.2
        expected = (12.0 - 10.0) / (0.2 * 10.0)
        np.testing.assert_allclose(compute_iwres(dv, ipred, sigma), [expected], rtol=1e-10)

    def test_negative_residual(self):
        dv = np.array([8.0])
        ipred = np.array([10.0])
        iwres = compute_iwres(dv, ipred, sigma=1.0)
        assert iwres[0] < 0.0

    def test_zero_ipred_returns_zero(self):
        dv = np.array([5.0])
        ipred = np.array([0.0])
        iwres = compute_iwres(dv, ipred, sigma=1.0)
        assert iwres[0] == 0.0  # avoids divide-by-zero

    def test_shape_mismatch_raises(self):
        with pytest.raises(ValueError, match="same shape"):
            compute_iwres(np.array([1.0, 2.0]), np.array([1.0]))

    def test_sigma_le_zero_raises(self):
        with pytest.raises(ValueError, match="sigma must be > 0"):
            compute_iwres(np.array([1.0]), np.array([1.0]), sigma=0.0)


class TestObsPredMetrics:
    def test_perfect_prediction_rmse_zero(self):
        """When DV == PRED, RMSE == 0 and MPE == 0."""
        dv = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        m = obs_pred_metrics(dv, dv.copy())
        assert math.isclose(m["RMSE"], 0.0, abs_tol=1e-12)
        assert math.isclose(m["MPE"], 0.0, abs_tol=1e-12)

    def test_perfect_prediction_r2_one(self):
        dv = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        m = obs_pred_metrics(dv, dv.copy())
        assert math.isclose(m["R2"], 1.0, abs_tol=1e-12)

    def test_constant_pred_r2_zero(self):
        """Predicting mean(DV) everywhere gives R2 == 0."""
        dv = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        pred = np.full_like(dv, dv.mean())
        m = obs_pred_metrics(dv, pred)
        assert math.isclose(m["R2"], 0.0, abs_tol=1e-10)

    def test_known_rmse(self):
        """RMSE of [1,2,3] vs [2,2,2] = sqrt((1+0+1)/3) = sqrt(2/3)."""
        dv = np.array([1.0, 2.0, 3.0])
        pred = np.array([2.0, 2.0, 2.0])
        expected_rmse = math.sqrt(2.0 / 3.0)
        m = obs_pred_metrics(dv, pred)
        assert math.isclose(m["RMSE"], expected_rmse, rel_tol=1e-10)

    def test_n_field(self):
        dv = np.array([1.0, 2.0, 3.0])
        m = obs_pred_metrics(dv, dv.copy())
        assert m["n"] == 3.0


class TestGOFResult:
    def _make_result(self, n=10):
        rng = np.random.default_rng(42)
        dv = rng.uniform(1.0, 20.0, n)
        ipred = dv * (1.0 + rng.normal(0, 0.1, n))
        pred = dv * (1.0 + rng.normal(0, 0.2, n))
        time = np.linspace(0.5, 10.0, n)
        id_ = [f"S{i % 3 + 1}" for i in range(n)]
        return GOFResult(
            dv=dv.tolist(),
            pred=pred.tolist(),
            ipred=ipred.tolist(),
            time=time.tolist(),
            id=id_,
            sigma=0.15,
            study_label="Test Study",
        )

    def test_iwres_shape(self):
        r = self._make_result()
        assert len(r.iwres) == 10

    def test_iwres_degenerate(self):
        """If DV == IPRED, all IWRES must be 0."""
        dv = [5.0, 10.0, 15.0]
        r = GOFResult(
            dv=dv, pred=dv, ipred=dv, time=[1.0, 2.0, 3.0], id=["S1", "S1", "S1"], sigma=1.0
        )
        np.testing.assert_allclose(r.iwres, 0.0, atol=1e-12)

    def test_summary_contains_study_label(self):
        r = self._make_result()
        assert "Test Study" in r.summary()

    def test_to_dataframe_columns(self):
        r = self._make_result()
        df = r.to_dataframe()
        assert set(["ID", "TIME", "DV", "PRED", "IPRED", "IWRES"]).issubset(df.columns)
        assert len(df) == 10

    def test_mismatched_array_lengths_raise(self):
        with pytest.raises(ValueError, match="same length"):
            GOFResult(dv=[1.0, 2.0], pred=[1.0], ipred=[1.0, 2.0], time=[1.0, 2.0], id=["S1", "S1"])

    def test_html_report(self, tmp_path):
        r = self._make_result()
        out = tmp_path / "gof.html"
        html = r.report(out, format="html")
        assert out.exists()
        assert "GOF" in html
        assert "OpenPKFlow" in html

    def test_markdown_report(self, tmp_path):
        r = self._make_result()
        out = tmp_path / "gof.md"
        md = r.report(out, format="markdown")
        assert out.exists()
        assert "RMSE" in md
