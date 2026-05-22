"""Tests for dissolution model fitting (v0.2.0).

Validation discipline per CLAUDE.md:
  1. Degenerate/sanity case: generate noise-free profile from known params
     -> fit -> recover to within tolerance.
  2. Reference: Costa P, Lobo JMS (2001) Eur J Pharm Sci, 13(2):123-133.
     DOI: 10.1016/S0928-0987(01)00095-1
"""

from __future__ import annotations

import math
import warnings

import numpy as np
import pytest

from openpkflow.dissolution.models import (
    VALID_MODELS,
    DissolutionFitResults,
    ModelFit,
    _first_order,
    _higuchi,
    _korsmeyer_peppas,
    _weibull,
    _zero_order,
    fit_dissolution_models,
)

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _assert_params_close(fit: ModelFit, expected: dict[str, float], rel_tol: float = 1e-3) -> None:
    assert fit.converged, f"Model '{fit.model_name}' did not converge"
    for name, exp_val in expected.items():
        got = fit.params[name]
        assert math.isclose(got, exp_val, rel_tol=rel_tol), (
            f"{fit.model_name}: param '{name}' = {got:.6g}, expected {exp_val:.6g} "
            f"(rel_tol={rel_tol})"
        )


# ──────────────────────────────────────────────────────────────────────────────
# Degenerate recovery: noise-free profile -> fit -> recover known params
# Reference: Costa & Lobo (2001) — each model section validates the functional
# form by confirming the fitter recovers the generating parameters.
# ──────────────────────────────────────────────────────────────────────────────


class TestZeroOrderDegenerate:
    """Zero-order model: Q(t) = k0 * t.  Degenerate recovery test."""

    def test_recover_k0(self) -> None:
        k0_true = 2.0
        t = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        Q = _zero_order(t, k0_true)

        results = fit_dissolution_models(t.tolist(), Q.tolist(), "test", models=["zero_order"])
        fit = results.fits[0]
        _assert_params_close(fit, {"k0": k0_true})

    def test_metrics_finite(self) -> None:
        t = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        Q = _zero_order(t, 1.8)
        results = fit_dissolution_models(t.tolist(), Q.tolist(), "test", models=["zero_order"])
        fit = results.fits[0]
        assert math.isfinite(fit.r_squared)
        assert math.isfinite(fit.aicc)
        assert math.isfinite(fit.bic)
        assert fit.r_squared > 0.999


class TestFirstOrderDegenerate:
    """First-order model: Q(t) = 100 * (1 - exp(-k1 * t)).  Degenerate recovery."""

    def test_recover_k1(self) -> None:
        k1_true = 0.08
        t = np.array([5.0, 15.0, 30.0, 45.0, 60.0])
        Q = _first_order(t, k1_true)

        results = fit_dissolution_models(t.tolist(), Q.tolist(), "test", models=["first_order"])
        fit = results.fits[0]
        _assert_params_close(fit, {"k1": k1_true})

    def test_r_squared_near_one(self) -> None:
        t = np.array([5.0, 15.0, 30.0, 45.0, 60.0])
        Q = _first_order(t, 0.05)
        results = fit_dissolution_models(t.tolist(), Q.tolist(), "test", models=["first_order"])
        assert results.fits[0].r_squared > 0.999


class TestHiguchiDegenerate:
    """Higuchi model: Q(t) = kH * sqrt(t).  Degenerate recovery.

    Reference: Costa & Lobo (2001), Section 2.3 — matrix diffusion model.
    """

    def test_recover_kH(self) -> None:
        kH_true = 10.0
        t = np.array([1.0, 4.0, 9.0, 16.0, 25.0])
        Q = _higuchi(t, kH_true)  # Q = [10, 20, 30, 40, 50] — hand-checkable

        results = fit_dissolution_models(t.tolist(), Q.tolist(), "test", models=["higuchi"])
        fit = results.fits[0]
        _assert_params_close(fit, {"kH": kH_true})

    def test_hand_checkable_values(self) -> None:
        """kH=10, t=[1,4,9,16,25] -> Q=[10,20,30,40,50] exactly (sqrt law)."""
        t = np.array([1.0, 4.0, 9.0, 16.0, 25.0])
        expected_Q = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        np.testing.assert_allclose(_higuchi(t, 10.0), expected_Q, rtol=1e-12)


class TestKorsmeyerPeppasDegnerate:
    """Korsmeyer-Peppas: Q(t) = k * t^n.  Degenerate recovery.

    Reference: Costa & Lobo (2001), Section 2.5 — power-law model.
    Note: n < 0.45 Fickian diffusion, 0.45-0.89 anomalous, > 0.89 Case II.
    """

    def test_recover_k_and_n(self) -> None:
        k_true, n_true = 5.0, 0.7
        t = np.array([5.0, 10.0, 15.0, 20.0, 25.0])
        Q = _korsmeyer_peppas(t, k_true, n_true)  # all < 60%, no warning

        results = fit_dissolution_models(
            t.tolist(), Q.tolist(), "test", models=["korsmeyer_peppas"]
        )
        fit = results.fits[0]
        _assert_params_close(fit, {"k": k_true, "n": n_true})

    def test_kp_60pct_warning(self) -> None:
        """Warn when more than one timepoint exceeds 60% release."""
        t = np.array([10.0, 20.0, 30.0, 45.0, 60.0])
        Q = np.array([50.0, 65.0, 75.0, 85.0, 92.0])  # 4 points > 60%

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            fit_dissolution_models(t.tolist(), Q.tolist(), "test", models=["korsmeyer_peppas"])

        kp_warnings = [x for x in w if "Korsmeyer-Peppas" in str(x.message)]
        assert len(kp_warnings) == 1

    def test_kp_no_warning_one_point_above_60(self) -> None:
        """No warning when <= 1 point exceeds 60%."""
        t = np.array([5.0, 10.0, 15.0, 20.0, 25.0])
        Q = np.array([20.0, 35.0, 48.0, 58.0, 62.0])  # only 1 point > 60%

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            fit_dissolution_models(t.tolist(), Q.tolist(), "test", models=["korsmeyer_peppas"])

        kp_warnings = [x for x in w if "Korsmeyer-Peppas" in str(x.message)]
        assert len(kp_warnings) == 0


class TestWeibullDegenerate:
    """Weibull model: Q(t) = 100 * (1 - exp(-(t/beta)^alpha)).  Degenerate recovery.

    Reference: Costa & Lobo (2001), Section 2.6 — Weibull model.
    Note: Weibull is empirical; FDA/EMA do not recommend it for IVIVC without
    mechanistic justification.
    """

    def test_recover_alpha_beta(self) -> None:
        alpha_true, beta_true = 1.5, 30.0
        t = np.array([10.0, 20.0, 30.0, 45.0, 60.0, 75.0, 90.0])
        Q = _weibull(t, alpha_true, beta_true)

        results = fit_dissolution_models(t.tolist(), Q.tolist(), "test", models=["weibull"])
        fit = results.fits[0]
        _assert_params_close(fit, {"alpha": alpha_true, "beta": beta_true}, rel_tol=1e-3)

    def test_r_squared_near_one(self) -> None:
        t = np.array([10.0, 20.0, 30.0, 45.0, 60.0, 75.0, 90.0])
        Q = _weibull(t, 1.2, 25.0)
        results = fit_dissolution_models(t.tolist(), Q.tolist(), "test", models=["weibull"])
        assert results.fits[0].r_squared > 0.999


# ──────────────────────────────────────────────────────────────────────────────
# Cross-model AICc ranking
# ──────────────────────────────────────────────────────────────────────────────


class TestAICcRanking:
    """AICc-based model selection.

    With noise-free Weibull-generated data (alpha=1.5, beta=20), the Weibull
    model achieves near-zero RSS and should rank first by AICc.
    """

    def test_weibull_ranks_first_on_weibull_data(self) -> None:
        alpha, beta = 1.5, 20.0
        t = np.linspace(2.0, 80.0, 15)
        Q = _weibull(t, alpha, beta)

        results = fit_dissolution_models(
            t.tolist(),
            Q.tolist(),
            "test",
            models=["zero_order", "first_order", "higuchi", "korsmeyer_peppas", "weibull"],
        )

        assert results.best.model_name == "weibull"

    def test_first_order_ranks_first_on_first_order_data(self) -> None:
        t = np.array([5.0, 15.0, 30.0, 45.0, 60.0, 90.0, 120.0])
        Q = _first_order(t, 0.06)

        results = fit_dissolution_models(
            t.tolist(),
            Q.tolist(),
            "test",
            models=["first_order", "higuchi", "zero_order"],
        )
        assert results.best.model_name == "first_order"

    def test_higuchi_ranks_first_on_higuchi_data(self) -> None:
        t = np.array([1.0, 4.0, 9.0, 16.0, 25.0, 36.0, 49.0])
        Q = _higuchi(t, 8.5)

        results = fit_dissolution_models(
            t.tolist(),
            Q.tolist(),
            "test",
            models=["first_order", "higuchi", "zero_order"],
        )
        assert results.best.model_name == "higuchi"


# ──────────────────────────────────────────────────────────────────────────────
# DissolutionFitResults API
# ──────────────────────────────────────────────────────────────────────────────


class TestDissolutionFitResults:
    def _make_results(self) -> DissolutionFitResults:
        t = np.array([5.0, 15.0, 30.0, 45.0, 60.0])
        Q = _first_order(t, 0.07)
        return fit_dissolution_models(
            t.tolist(), Q.tolist(), "ref", models=["first_order", "higuchi"]
        )

    def test_best_returns_modelfit(self) -> None:
        results = self._make_results()
        best = results.best
        assert isinstance(best, ModelFit)
        assert best.converged

    def test_summary_is_string(self) -> None:
        results = self._make_results()
        s = results.summary()
        assert isinstance(s, str)
        assert "Formulation" in s
        assert "AICc" in s
        assert "BEST" in s

    def test_summary_ascii_only(self) -> None:
        results = self._make_results()
        s = results.summary()
        s.encode("ascii")  # raises UnicodeEncodeError if any non-ASCII present

    def test_to_dict_keys(self) -> None:
        results = self._make_results()
        d = results.to_dict()
        assert set(d.keys()) == {"formulation_label", "time_points", "observed_mean", "fits"}
        assert d["formulation_label"] == "ref"

    def test_predict_roundtrip(self) -> None:
        t = np.array([5.0, 15.0, 30.0, 45.0, 60.0])
        Q = _first_order(t, 0.07)
        results = fit_dissolution_models(t.tolist(), Q.tolist(), "ref", models=["first_order"])
        fit = results.fits[0]
        Q_pred = fit.predict(t)
        np.testing.assert_allclose(Q_pred, Q, rtol=1e-3)

    def test_predict_raises_if_not_converged(self) -> None:
        bad_fit = ModelFit(
            model_name="first_order",
            params={},
            r_squared=float("nan"),
            aic=float("nan"),
            aicc=float("nan"),
            bic=float("nan"),
            n_points=5,
            n_params=1,
            converged=False,
            fitted_values=[],
            time_points=[5.0, 15.0, 30.0, 45.0, 60.0],
        )
        with pytest.raises(RuntimeError, match="did not converge"):
            bad_fit.predict(np.array([10.0, 20.0]))

    def test_best_raises_if_none_converged(self) -> None:
        bad_fit = ModelFit(
            model_name="first_order",
            params={},
            r_squared=float("nan"),
            aic=float("nan"),
            aicc=float("nan"),
            bic=float("nan"),
            n_points=5,
            n_params=1,
            converged=False,
            fitted_values=[],
            time_points=[5.0, 15.0, 30.0, 45.0, 60.0],
        )
        results = DissolutionFitResults(
            formulation_label="test",
            time_points=[5.0, 15.0, 30.0, 45.0, 60.0],
            observed_mean=[10.0, 30.0, 55.0, 72.0, 85.0],
            fits=[bad_fit],
        )
        with pytest.raises(ValueError, match="No models converged"):
            _ = results.best

    def test_plot_saves_file(self, tmp_path) -> None:
        results = self._make_results()
        out = tmp_path / "fit.png"
        results.plot(output_path=str(out), show=False)
        assert out.exists()
        assert out.stat().st_size > 0

    def test_report_html_saves_file(self, tmp_path) -> None:
        results = self._make_results()
        out = tmp_path / "fit.html"
        html = results.report(str(out))
        assert out.exists()
        assert "Dissolution Model Fitting" in html
        assert "AICc" in html

    def test_report_unsupported_format_raises(self) -> None:
        results = self._make_results()
        with pytest.raises(ValueError, match="docx"):
            results.report("out.pptx", format="pptx")


# ──────────────────────────────────────────────────────────────────────────────
# fit_dissolution_models() validation
# ──────────────────────────────────────────────────────────────────────────────


class TestFitDissolutionModelsValidation:
    def test_unknown_model_raises(self) -> None:
        t = [10.0, 20.0, 30.0, 40.0, 50.0]
        Q = [20.0, 40.0, 55.0, 68.0, 78.0]
        with pytest.raises(ValueError, match="Unknown model"):
            fit_dissolution_models(t, Q, "test", models=["banana"])

    def test_too_few_timepoints_raises(self) -> None:
        with pytest.raises(ValueError, match="3 timepoints"):
            fit_dissolution_models([10.0, 20.0], [30.0, 60.0], "test")

    def test_mismatched_lengths_raises(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            fit_dissolution_models([10.0, 20.0, 30.0], [20.0, 40.0], "test")

    def test_all_default_models_fit(self) -> None:
        t = np.array([5.0, 15.0, 30.0, 45.0, 60.0, 90.0])
        Q = _first_order(t, 0.06)
        results = fit_dissolution_models(t.tolist(), Q.tolist(), "test")
        assert len(results.fits) == 5
        assert all(f.model_name in VALID_MODELS for f in results.fits)

    def test_formulation_label_preserved(self) -> None:
        t = [10.0, 20.0, 30.0, 40.0, 50.0]
        Q = [20.0, 38.0, 54.0, 67.0, 78.0]
        results = fit_dissolution_models(t, Q, "my_formulation")
        assert results.formulation_label == "my_formulation"

    def test_single_model_subset(self) -> None:
        t = [10.0, 20.0, 30.0, 40.0, 50.0]
        Q = [20.0, 38.0, 54.0, 67.0, 78.0]
        results = fit_dissolution_models(t, Q, "test", models=["first_order"])
        assert len(results.fits) == 1
        assert results.fits[0].model_name == "first_order"

    def test_aicc_lower_than_aic_for_small_n(self) -> None:
        """AICc correction adds a positive penalty when n is small."""
        t = [10.0, 20.0, 30.0, 40.0, 50.0]
        Q = _first_order(np.array(t), 0.06).tolist()
        results = fit_dissolution_models(t, Q, "test", models=["first_order"])
        fit = results.fits[0]
        # AICc >= AIC always (positive correction)
        assert fit.aicc >= fit.aic - 1e-9


# ──────────────────────────────────────────────────────────────────────────────
# DissolutionStudy.fit_models() integration
# ──────────────────────────────────────────────────────────────────────────────


class TestStudyFitModels:
    def test_fit_models_from_csv(self) -> None:
        from openpkflow.datasets import example_dissolution_path
        from openpkflow.dissolution import DissolutionStudy

        study = DissolutionStudy.from_csv(example_dissolution_path())
        formulations = study.formulations()
        results = study.fit_models(formulations[0], models=["first_order", "higuchi"])
        assert isinstance(results, DissolutionFitResults)
        assert len(results.fits) == 2

    def test_fit_models_unknown_formulation_raises(self) -> None:
        from openpkflow.datasets import example_dissolution_path
        from openpkflow.dissolution import DissolutionStudy

        study = DissolutionStudy.from_csv(example_dissolution_path())
        with pytest.raises(ValueError, match="not found"):
            study.fit_models("nonexistent_formulation")
