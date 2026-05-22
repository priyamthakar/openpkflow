"""Tests for openpkflow.dissolution.models — model_dependent_comparison.

Reference
---------
FDA Guidance for Industry: Dissolution Testing of Immediate Release Solid
Oral Dosage Forms (1997). CDER. Section on model-dependent approaches.
"""

from __future__ import annotations

import numpy as np
import pytest

from openpkflow.dissolution.models import (
    ModelComparisonResult,
    model_dependent_comparison,
)


# Synthetic first-order profiles with known rate constants
def _first_order_profile(t: np.ndarray, k: float, noise: float = 0.0) -> np.ndarray:
    np.random.seed(42)
    Q = 100.0 * (1.0 - np.exp(-k * t))
    if noise > 0:
        Q = Q + np.random.normal(0, noise, len(t))
    return np.clip(Q, 0.0, 100.0)


class TestModelDependentComparison:
    def test_identical_profiles(self) -> None:
        """Identical profiles (same k=0.04) should give ratio ≈ 100% and SIMILAR verdict."""
        t = np.linspace(5, 120, 12)
        Q = _first_order_profile(t, 0.04)
        result = model_dependent_comparison(t, Q, t, Q, "first_order")
        assert result.ratio_pct == pytest.approx(100.0, abs=10.0)
        assert result.is_similar is True

    def test_mildly_different_profiles(self) -> None:
        """k=0.04 vs k=0.036: ratio ~90%, should still be similar."""
        t = np.linspace(5, 120, 12)
        Qr = _first_order_profile(t, 0.04)
        Qt = _first_order_profile(t, 0.036)
        result = model_dependent_comparison(t, Qr, t, Qt, "first_order")
        assert result.ratio_pct > 80.0
        assert result.ratio_pct < 120.0

    def test_returns_model_comparison_result(self) -> None:
        t = np.linspace(5, 120, 8)
        Q = _first_order_profile(t, 0.04)
        result = model_dependent_comparison(t, Q, t, Q, "first_order")
        assert isinstance(result, ModelComparisonResult)

    def test_model_name_stored(self) -> None:
        t = np.linspace(5, 120, 8)
        Q = _first_order_profile(t, 0.04)
        result = model_dependent_comparison(t, Q, t, Q, "first_order")
        assert result.model_name == "first_order"

    def test_summary_contains_verdict(self) -> None:
        t = np.linspace(5, 120, 8)
        Qr = _first_order_profile(t, 0.04)
        Qt = _first_order_profile(t, 0.036)
        result = model_dependent_comparison(t, Qr, t, Qt, "first_order")
        text = result.summary()
        assert "SIMILAR" in text

    def test_weibull_model(self) -> None:
        """model_dependent_comparison works with Weibull model (2-param)."""
        np.random.seed(123)
        t = np.linspace(5, 120, 15)
        Qr = 100.0 * (1.0 - np.exp(-((t / 30.0) ** 1.5))) + np.random.normal(0, 0.5, 15)
        Qt = 100.0 * (1.0 - np.exp(-((t / 32.0) ** 1.5))) + np.random.normal(0, 0.5, 15)
        result = model_dependent_comparison(t, Qr, t, Qt, "weibull", param_index=1)
        assert result.model_name == "weibull"
        assert result.ratio_pct > 0.0

    def test_narrower_ci_range(self) -> None:
        """With a tighter 90-111.11% window, a mild difference may fail."""
        t = np.linspace(5, 120, 8)
        Qr = _first_order_profile(t, 0.04)
        Qt = _first_order_profile(t, 0.035)
        result = model_dependent_comparison(
            t,
            Qr,
            t,
            Qt,
            "first_order",
            ci_range=(90.0, 111.11),
        )
        # The stricter window may or may not pass depending on fit, but it should complete
        assert isinstance(result.is_similar, bool)

    def test_summary_text(self) -> None:
        t = np.linspace(5, 120, 8)
        Qr = _first_order_profile(t, 0.04)
        Qt = _first_order_profile(t, 0.028)
        result = model_dependent_comparison(t, Qr, t, Qt, "first_order")
        assert "Model:" in result.summary()
        assert "Param:" in result.summary()
        assert "90% CI" in result.summary()
        assert "Verdict:" in result.summary()

    # Error cases
    def test_raises_on_unknown_model(self) -> None:
        t = np.linspace(5, 120, 8)
        Q = _first_order_profile(t, 0.04)
        with pytest.raises(ValueError, match="Unknown model"):
            model_dependent_comparison(t, Q, t, Q, "nonexistent_model")

    def test_raises_on_too_few_timepoints(self) -> None:
        t = np.array([5.0, 60.0])
        Q = _first_order_profile(t, 0.04)
        with pytest.raises(ValueError, match="At least 3"):
            model_dependent_comparison(t, Q, t, Q, "first_order")

    def test_raises_on_bad_param_index(self) -> None:
        t = np.linspace(5, 120, 8)
        Q = _first_order_profile(t, 0.04)
        with pytest.raises(ValueError, match="out of range"):
            model_dependent_comparison(t, Q, t, Q, "first_order", param_index=5)
