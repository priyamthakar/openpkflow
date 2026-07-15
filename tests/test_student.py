"""Tests for the student-friendly API layer (openpkflow.student).

Tests the one-liner functions: fit_dissolution(), analyze_pk(), fit_pk_model().
Uses the bundled example datasets and synthetic data for edge cases.
"""

from __future__ import annotations

import math
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from openpkflow.student import (
    DissolutionAnalysis,
    NCAAnalysis,
    PKModelFit,
    analyze_pk,
    fit_dissolution,
    fit_pk_model,
)

# ---------------------------------------------------------------------------
# Paths to bundled datasets
# ---------------------------------------------------------------------------

_DATASETS = Path(__file__).resolve().parent.parent / "src" / "openpkflow" / "datasets"
DISSOLUTION_CSV = _DATASETS / "example_dissolution.csv"
THEOPH_CSV = _DATASETS / "theoph.csv"


# ===================================================================
# fit_dissolution() tests
# ===================================================================


class TestFitDissolution:
    """Tests for the student-friendly dissolution analysis."""

    def test_load_csv_and_fit(self):
        """fit_dissolution loads CSV, fits models, returns DissolutionAnalysis."""
        result = fit_dissolution(DISSOLUTION_CSV)
        assert isinstance(result, DissolutionAnalysis)
        assert len(result.formulations) >= 1
        assert len(result.fits) >= 1

    def test_models_converge(self):
        """At least 4 of 6 models should converge on example data."""
        result = fit_dissolution(DISSOLUTION_CSV)
        for label, fit_result in result.fits.items():
            n_converged = sum(1 for f in fit_result.fits if f.converged)
            assert n_converged >= 4, f"Only {n_converged} models converged for '{label}'"

    def test_best_model_has_aicc(self):
        """The best model should have a finite AICc."""
        result = fit_dissolution(DISSOLUTION_CSV)
        for _label, fit_result in result.fits.items():
            best = fit_result.best
            assert math.isfinite(best.aicc)
            assert best.converged

    def test_comparison_auto_detected(self):
        """With exactly 2 formulations, comparison should be auto-detected."""
        result = fit_dissolution(DISSOLUTION_CSV)
        assert result.comparison is not None
        assert result.comparison.f2_value >= 0  # f2 is always >= 0 for valid data

    def test_comparison_explicit(self):
        """Explicit reference/test labels should work."""
        result = fit_dissolution(DISSOLUTION_CSV, reference="reference", test="test")
        assert result.comparison is not None

    def test_summary_returns_string(self):
        """summary() should return a non-empty string."""
        result = fit_dissolution(DISSOLUTION_CSV)
        text = result.summary()
        assert isinstance(text, str)
        assert len(text) > 100
        assert "DISSOLUTION" in text

    def test_plot_saves_file(self):
        """plot() should save a PNG file."""
        result = fit_dissolution(DISSOLUTION_CSV)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            path = f.name
        result.plot(output_path=path)
        assert Path(path).exists()
        assert Path(path).stat().st_size > 1000

    def test_from_dataframe(self):
        """fit_dissolution should accept a DataFrame directly."""
        df = pd.read_csv(DISSOLUTION_CSV)
        result = fit_dissolution(df)
        assert isinstance(result, DissolutionAnalysis)

    def test_custom_models(self):
        """Custom model list should be respected."""
        result = fit_dissolution(DISSOLUTION_CSV, models=["first_order", "weibull"])
        for fit_result in result.fits.values():
            model_names = {f.model_name for f in fit_result.fits}
            assert model_names == {"first_order", "weibull"}

    def test_file_not_found(self):
        """Missing file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            fit_dissolution("nonexistent_file.csv")

    def test_missing_columns(self):
        """CSV without required columns should raise ValueError."""
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            df.to_csv(f.name, index=False)
            with pytest.raises(ValueError, match="formulation"):
                fit_dissolution(f.name)

    def test_column_name_aliases(self):
        """Various column name aliases should be recognized."""
        df = pd.DataFrame(
            {
                "Product": ["A", "A", "A", "B", "B", "B"],
                "t": [5, 15, 30, 5, 15, 30],
                "%Dissolved": [20, 55, 85, 22, 52, 80],
            }
        )
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            df.to_csv(f.name, index=False)
            result = fit_dissolution(f.name)
            assert len(result.formulations) == 2


# ===================================================================
# analyze_pk() tests
# ===================================================================


class TestAnalyzePK:
    """Tests for the student-friendly NCA analysis."""

    def test_load_theoph_and_analyze(self):
        """analyze_pk should run NCA on the Theophylline dataset."""
        result = analyze_pk(THEOPH_CSV)
        assert isinstance(result, NCAAnalysis)
        assert result.summary_results is not None
        assert len(result.summary_results.results) == 12

    def test_summary_returns_string(self):
        """summary() should return a formatted table."""
        result = analyze_pk(THEOPH_CSV)
        text = result.summary()
        assert "NCA" in text
        assert "AUClast" in text
        assert "Subject" in text

    def test_to_dataframe(self):
        """to_dataframe() should return a DataFrame with NCA columns."""
        result = analyze_pk(THEOPH_CSV)
        df = result.to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 12
        assert "AUClast" in df.columns
        assert "Cmax" in df.columns

    def test_plot_saves_file(self):
        """plot() should save a PNG file."""
        result = analyze_pk(THEOPH_CSV)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            path = f.name
        result.plot(output_path=path)
        assert Path(path).exists()
        assert Path(path).stat().st_size > 1000

    def test_from_dataframe(self):
        """analyze_pk should accept a DataFrame directly."""
        df = pd.read_csv(THEOPH_CSV)
        result = analyze_pk(df)
        assert isinstance(result, NCAAnalysis)

    def test_column_aliases(self):
        """Various column name aliases should be recognized."""
        df = pd.DataFrame(
            {
                "ID": [1, 1, 1, 1],
                "hour": [0, 1, 2, 4],
                "concentration": [0, 5.0, 3.0, 1.0],
                "amt": [100, 100, 100, 100],
            }
        )
        result = analyze_pk(df)
        assert result.summary_results is not None
        assert len(result.summary_results.results) == 1

    def test_auc_method_options(self):
        """Different AUC methods should all work."""
        for method in ["linear", "log", "linear_up_log_down"]:
            result = analyze_pk(THEOPH_CSV, auc_method=method)
            assert result.summary_results is not None
            assert result.summary_results.auc_method == method

    def test_file_not_found(self):
        """Missing file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            analyze_pk("nonexistent_pk_data.csv")

    def test_missing_columns(self):
        """CSV without required columns should raise ValueError."""
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            df.to_csv(f.name, index=False)
            with pytest.raises(ValueError, match="subject"):
                analyze_pk(f.name)

    def test_subjects_populated(self):
        """subjects dict should contain SubjectProfile objects."""
        result = analyze_pk(THEOPH_CSV)
        assert len(result.subjects) == 12
        for _subj_id, prof in result.subjects.items():
            assert len(prof.times) > 0
            assert len(prof.concs) > 0
            assert prof.dose > 0


# ===================================================================
# fit_pk_model() tests
# ===================================================================


class TestFitPKModel:
    """Tests for the student-friendly PK model fitting."""

    def test_oral_1cmt_fit(self):
        """1-compartment oral fit should converge on clean synthetic data."""
        # Generate synthetic 1-cmt oral data
        t = np.array([0.5, 1, 2, 4, 8, 12, 24])
        k = 0.1
        ka = 1.0
        vz_f = 50.0
        dose = 100.0
        c = (dose * ka) / (vz_f * (ka - k)) * (np.exp(-k * t) - np.exp(-ka * t))

        result = fit_pk_model(t, c, dose=dose, route="oral", model="1-compartment")
        assert isinstance(result, PKModelFit)
        assert result.converged
        assert result.r_squared > 0.99

    def test_iv_1cmt_fit(self):
        """1-compartment IV bolus fit should converge."""
        t = np.array([0.5, 1, 2, 4, 8, 12])
        cl, vz = 5.0, 50.0
        dose = 500.0
        c = (dose / vz) * np.exp(-cl / vz * t)

        result = fit_pk_model(t, c, dose=dose, route="iv_bolus", model="1-compartment")
        assert result.converged
        assert result.r_squared > 0.99

    def test_oral_2cmt_fit(self):
        """2-compartment oral fit should converge on clean data."""
        # Generate from 2-cmt oral model
        from openpkflow.student.sim import _oral_2cmt

        t = np.array([0.5, 1, 2, 4, 6, 8, 12, 24])
        dose = 100.0
        c = _oral_2cmt(t, dose, CL_F=5.0, V1_F=30.0, Q=2.0, V2=50.0, ka=1.5)

        result = fit_pk_model(t, c, dose=dose, route="oral", model="2-compartment")
        assert result.converged
        assert result.r_squared > 0.95

    def test_predict(self):
        """predict() should return concentrations at new time points."""
        t = np.array([0.5, 1, 2, 4, 8, 12, 24])
        k, ka, vz_f = 0.1, 1.0, 50.0
        dose = 100.0
        c = (dose * ka) / (vz_f * (ka - k)) * (np.exp(-k * t) - np.exp(-ka * t))

        result = fit_pk_model(t, c, dose=dose, route="oral")
        t_new = np.array([3, 6, 10])
        c_new = result.predict(t_new)
        assert len(c_new) == 3
        assert all(c_new > 0)

    def test_summary_string(self):
        """summary() should return formatted text with parameter table."""
        t = np.array([0.5, 1, 2, 4, 8, 12])
        k, ka, vz_f = 0.1, 1.0, 50.0
        dose = 100.0
        c = (dose * ka) / (vz_f * (ka - k)) * (np.exp(-k * t) - np.exp(-ka * t))

        result = fit_pk_model(t, c, dose=dose, route="oral")
        text = result.summary()
        assert "1-COMPARTMENT" in text
        assert "CL_F" in text or "CL" in text

    def test_plot_saves_file(self):
        """plot() should save a PNG file."""
        t = np.array([0.5, 1, 2, 4, 8, 12])
        k, ka, vz_f = 0.1, 1.0, 50.0
        dose = 100.0
        c = (dose * ka) / (vz_f * (ka - k)) * (np.exp(-k * t) - np.exp(-ka * t))

        result = fit_pk_model(t, c, dose=dose, route="oral")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            path = f.name
        result.plot(output_path=path)
        assert Path(path).exists()
        assert Path(path).stat().st_size > 1000

    def test_half_life_property(self):
        """half_life property should be close to ln(2)/k for 1-cmt oral."""
        t = np.array([0.5, 1, 2, 4, 8, 12, 24])
        k = 0.1
        ka = 1.0
        vz_f = 50.0
        dose = 100.0
        expected_hl = math.log(2) / k  # ~6.93
        c = (dose * ka) / (vz_f * (ka - k)) * (np.exp(-k * t) - np.exp(-ka * t))

        result = fit_pk_model(t, c, dose=dose, route="oral")
        assert result.half_life is not None
        assert abs(result.half_life - expected_hl) / expected_hl < 0.1  # within 10%

    def test_length_mismatch_raises(self):
        """Mismatched times/concs should raise ValueError."""
        with pytest.raises(ValueError, match="same length"):
            fit_pk_model([1, 2, 3], [1, 2], dose=100)

    def test_too_few_points_raises(self):
        """Fewer than 3 points should raise ValueError."""
        with pytest.raises(ValueError, match="at least 3"):
            fit_pk_model([1, 2], [3, 4], dose=100)

    def test_negative_concs_raises(self):
        """Negative concentrations should raise ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            fit_pk_model([1, 2, 3], [1, -1, 2], dose=100)

    def test_invalid_route_raises(self):
        """Unsupported routes should not be treated as IV bolus."""
        with pytest.raises(ValueError, match="route must be"):
            fit_pk_model([1, 2, 3], [3, 2, 1], dose=100, route="iv")  # type: ignore[arg-type]

    def test_noisy_data_graceful(self):
        """Noisy data should still converge (or fail gracefully)."""
        np.random.seed(42)
        t = np.array([0.5, 1, 2, 4, 8, 12, 24])
        k, ka, vz_f = 0.1, 1.0, 50.0
        dose = 100.0
        c_clean = (dose * ka) / (vz_f * (ka - k)) * (np.exp(-k * t) - np.exp(-ka * t))
        c_noisy = c_clean + np.random.normal(0, 0.3, len(t))
        c_noisy = np.clip(c_noisy, 0, None)

        result = fit_pk_model(t, c_noisy, dose=dose, route="oral")
        # Should either converge or fail gracefully (no crash)
        assert isinstance(result, PKModelFit)
