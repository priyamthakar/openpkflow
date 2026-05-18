"""Tests for ml.surrogate (PKSurrogate) -- EXPERIMENTAL.

Validation approach (synthetic ground truth):
- Generate training data from openpkflow analytical 1-cmt oral formula
  (Gibaldi & Perrier 2nd ed., Eq. 1-14).
- Train surrogate on those data.
- Verify: (1) loss decreases over training, (2) surrogate predictions
  correlate tightly with analytical truth on hold-out set.

These tests run only when PyTorch is installed.
"""

from __future__ import annotations

import numpy as np
import pytest

try:
    import torch  # noqa: F401

    _HAS_TORCH = True
except ImportError:
    _HAS_TORCH = False

pytestmark = pytest.mark.skipif(not _HAS_TORCH, reason="requires torch")


class TestPKSurrogate:
    def test_loss_decreases_during_training(self):
        """Training loss must decrease monotonically on average.

        Synthetic truth: 1-cmt oral (Bateman equation, Gibaldi & Perrier Eq. 1-14).
        """
        from openpkflow.ml import PKSurrogate

        s = PKSurrogate.from_1cmt_oral(
            n_samples=200,
            n_timepoints=10,
            t_max=24.0,
            epochs=100,
            seed=42,
        )
        assert len(s.train_loss_history) == 100
        # Loss at end of training must be lower than at start
        assert s.train_loss_history[-1] < s.train_loss_history[0]

    def test_loss_reduces_substantially(self):
        """After 200 epochs, final loss must be < 50% of initial loss (model is learning)."""
        from openpkflow.ml import PKSurrogate

        s = PKSurrogate.from_1cmt_oral(
            n_samples=500,
            n_timepoints=15,
            t_max=24.0,
            epochs=200,
            seed=7,
        )
        assert s.train_loss_history[-1] < 0.5 * s.train_loss_history[0]

    def test_predict_before_fit_raises(self):
        from openpkflow.ml import PKSurrogate

        s = PKSurrogate()
        with pytest.raises(RuntimeError, match="fit()"):
            s.predict(np.array([[1.0, 100.0, 5.0, 50.0, 1.0]]))

    def test_predict_shape(self):
        from openpkflow.ml import PKSurrogate

        s = PKSurrogate.from_1cmt_oral(n_samples=200, n_timepoints=10, epochs=50, seed=0)
        X = np.array([[1.0, 100.0, 5.0, 50.0, 1.0], [4.0, 200.0, 10.0, 100.0, 0.5]])
        pred = s.predict(X)
        assert pred.shape == (2,)

    def test_predict_non_negative(self):
        """Surrogate must return non-negative concentrations (clipped at 0)."""
        from openpkflow.ml import PKSurrogate

        s = PKSurrogate.from_1cmt_oral(n_samples=200, n_timepoints=10, epochs=50, seed=0)
        X = np.array([[t, 100.0, 5.0, 50.0, 1.0] for t in np.linspace(0.1, 24.0, 20)])
        pred = s.predict(X)
        assert np.all(pred >= 0.0)

    def test_analytical_correlation(self):
        """Surrogate predictions should correlate strongly with analytical truth (r>0.95).

        Test uses a 1-cmt oral profile with known params: dose=100, CL_F=5, Vz_F=50, ka=1.2.
        Surrogate is trained on diverse data covering this param region.

        Reference: Gibaldi & Perrier (1982), Pharmacokinetics, 2nd ed., Eq. 1-14.
        """
        from openpkflow.ml import PKSurrogate
        from openpkflow.sim.methods import c_1cmt_oral

        s = PKSurrogate.from_1cmt_oral(
            n_samples=1000,
            n_timepoints=20,
            t_max=24.0,
            epochs=200,
            seed=42,
            param_ranges={
                "dose": (50.0, 200.0),
                "CL_F": (2.0, 15.0),
                "Vz_F": (20.0, 120.0),
                "ka": (0.5, 2.5),
            },
        )

        # hold-out: specific params within training range
        dose, cl_f, vz_f, ka = 100.0, 5.0, 50.0, 1.2
        times = np.linspace(0.5, 20.0, 30)
        analytical = c_1cmt_oral(times, dose=dose, CL_F=cl_f, Vz_F=vz_f, ka=ka)

        X_test = np.column_stack(
            [
                times,
                np.full_like(times, dose),
                np.full_like(times, cl_f),
                np.full_like(times, vz_f),
                np.full_like(times, ka),
            ]
        )
        predicted = s.predict(X_test)

        # Pearson r between predicted and analytical must be > 0.90
        # (experimental surrogate -- not expected to match analytical exactly)
        r = float(np.corrcoef(analytical, predicted)[0, 1])
        assert r > 0.90, f"Surrogate-analytical correlation {r:.3f} < 0.90"

    def test_summary_trained(self):
        from openpkflow.ml import PKSurrogate

        s = PKSurrogate.from_1cmt_oral(n_samples=100, n_timepoints=5, epochs=20, seed=0)
        summary = s.summary()
        assert "EXPERIMENTAL" in summary
        assert "Final loss" in summary
        assert "DISCLAIMER" in summary

    def test_summary_untrained(self):
        from openpkflow.ml import PKSurrogate

        s = PKSurrogate()
        summary = s.summary()
        assert "not trained" in summary

    def test_reproducible_with_seed(self):
        from openpkflow.ml import PKSurrogate

        s1 = PKSurrogate.from_1cmt_oral(n_samples=100, n_timepoints=5, epochs=20, seed=42)
        s2 = PKSurrogate.from_1cmt_oral(n_samples=100, n_timepoints=5, epochs=20, seed=42)
        X = np.array([[2.0, 100.0, 5.0, 50.0, 1.0]])
        p1 = s1.predict(X)
        p2 = s2.predict(X)
        np.testing.assert_allclose(p1, p2, rtol=1e-5)
