"""Tests for ICH M13B RSD constraint warning in DissolutionStudy.compare().

ICH M13B requires RSD <= 8% at time points with mean percent released <= 60%.
This is stricter than the legacy FDA CV limits.
"""

from __future__ import annotations

import warnings

import pandas as pd

from openpkflow.dissolution.loader import DissolutionCSVConfig
from openpkflow.dissolution.study import _check_ich_m13b_rsd


@pd.api.extensions.register_dataframe_accessor("_test_attr")
class _TestAccessor:
    pass


class TestICHM13BRSD:
    def test_no_warning_when_rsd_below_8pct(self) -> None:
        """Profiles with tight RSD below 8% should produce no warnings."""
        df = pd.DataFrame(
            {
                "formulation": ["Ref", "Ref", "Ref", "Ref"],
                "batch": [1, 1, 2, 2],
                "time": [10, 10, 20, 20],
                "percent_released": [25.0, 26.0, 45.0, 46.0],
            }
        )
        cfg = DissolutionCSVConfig()
        issues = _check_ich_m13b_rsd(df, "Ref", cfg)
        assert issues == []

    def test_warns_when_rsd_exceeds_8pct_at_early_timepoint(self) -> None:
        """RSD of ~10% at t=10 (mean 30%) should trigger a warning."""
        df = pd.DataFrame(
            {
                "formulation": ["Ref", "Ref", "Ref"],
                "batch": [1, 2, 3],
                "time": [10, 10, 10],
                "percent_released": [30.0, 27.0, 33.0],
            }
        )
        cfg = DissolutionCSVConfig()
        issues = _check_ich_m13b_rsd(df, "Ref", cfg)
        assert len(issues) >= 1
        assert any("RSD" in w and "ICH M13B" in w for w in issues)

    def test_no_warning_when_mean_above_60pct(self) -> None:
        """ICH M13B RSD check only applies when mean <= 60%."""
        df = pd.DataFrame(
            {
                "formulation": ["Ref", "Ref", "Ref"],
                "batch": [1, 2, 3],
                "time": [10, 10, 10],
                "percent_released": [70.0, 60.0, 80.0],
            }
        )
        cfg = DissolutionCSVConfig()
        issues = _check_ich_m13b_rsd(df, "Ref", cfg)
        assert issues == []

    def test_single_vessel_skipped(self) -> None:
        """Single vessel at a timepoint cannot compute RSD, so no warning."""
        df = pd.DataFrame(
            {
                "formulation": ["Ref"],
                "batch": [1],
                "time": [5],
                "percent_released": [20.0],
            }
        )
        cfg = DissolutionCSVConfig()
        issues = _check_ich_m13b_rsd(df, "Ref", cfg)
        assert issues == []

    def test_integration_with_dissolution_study(self) -> None:
        """End-to-end: DissolutionStudy.compare() warns when ICH M13B RSD violated.

        Creates a 3-vessel dataset where RSD at t=5 (mean ~25%) is >8%.
        Three timepoints required for f2 computation.
        """
        from openpkflow.dissolution.study import DissolutionStudy

        df = pd.DataFrame(
            {
                "formulation": ["Ref", "Ref", "Ref", "Ref", "Ref", "Ref", "Ref", "Ref", "Ref"],
                "batch": [1, 2, 3, 1, 2, 3, 1, 2, 3],
                "time": [5, 5, 5, 15, 15, 15, 30, 30, 30],
                "percent_released": [23.0, 30.0, 22.0, 45.0, 48.0, 46.0, 70.0, 68.0, 72.0],
            }
        )

        df_tst = pd.DataFrame(
            {
                "formulation": [
                    "Test",
                    "Test",
                    "Test",
                    "Test",
                    "Test",
                    "Test",
                    "Test",
                    "Test",
                    "Test",
                ],
                "batch": [1, 2, 3, 1, 2, 3, 1, 2, 3],
                "time": [5, 5, 5, 15, 15, 15, 30, 30, 30],
                "percent_released": [24.0, 25.0, 24.5, 46.0, 47.0, 45.0, 69.0, 71.0, 70.0],
            }
        )

        study = DissolutionStudy(pd.concat([df, df_tst], ignore_index=True))

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            study.compare("Ref", "Test")
            ich_warnings = [x for x in w if "ICH M13B" in str(x.message)]
        assert len(ich_warnings) >= 1
