"""Tests for ICH M13B Step 2 absolute SD variability check.

ICH M13B Step 2 draft (2025-02-12) defines high variability as absolute
SD > 8% at any time point. When SD > 8%, point-estimate f2 alone is not
sufficient and bootstrap f2 CI is indicated.
"""

from __future__ import annotations

import warnings

import pandas as pd

from openpkflow.dissolution.loader import DissolutionCSVConfig
from openpkflow.dissolution.study import _check_ich_m13b_sd


class TestICHM13BSD:
    def test_no_warning_when_sd_below_8pct(self) -> None:
        """Profiles with absolute SD below 8% produce no warnings."""
        df = pd.DataFrame(
            {
                "formulation": ["Ref", "Ref", "Ref", "Ref"],
                "batch": [1, 1, 2, 2],
                "time": [10, 10, 20, 20],
                "percent_released": [25.0, 26.0, 45.0, 46.0],
            }
        )
        cfg = DissolutionCSVConfig()
        issues = _check_ich_m13b_sd(df, "Ref", cfg)
        assert issues == []

    def test_warns_when_sd_exceeds_8pct_any_timepoint(self) -> None:
        """Absolute SD > 8% at any time point triggers a warning.

        Hand-checkable: values 20, 30, 40 at one time -> mean=30, sample SD
        = 10 > 8.

        Reference: ICH M13B Step 2 draft (2025-02-12), high variability
        defined as SD > 8% at any time point.
        """
        df = pd.DataFrame(
            {
                "formulation": ["Ref", "Ref", "Ref"],
                "batch": [1, 2, 3],
                "time": [10, 10, 10],
                "percent_released": [20.0, 30.0, 40.0],
            }
        )
        cfg = DissolutionCSVConfig()
        issues = _check_ich_m13b_sd(df, "Ref", cfg)
        assert len(issues) >= 1
        assert any("SD=" in w and "ICH M13B" in w for w in issues)

    def test_warns_even_when_mean_above_60pct(self) -> None:
        """Step 2 applies absolute SD at all means, not only mean <= 60%.

        Reference: ICH M13B Step 2 draft - SD across all time points.
        """
        df = pd.DataFrame(
            {
                "formulation": ["Ref", "Ref", "Ref"],
                "batch": [1, 2, 3],
                "time": [45, 45, 45],
                "percent_released": [60.0, 75.0, 90.0],
            }
        )
        cfg = DissolutionCSVConfig()
        issues = _check_ich_m13b_sd(df, "Ref", cfg)
        assert len(issues) >= 1

    def test_single_vessel_skipped(self) -> None:
        """Single vessel at a timepoint cannot compute SD, so no warning."""
        df = pd.DataFrame(
            {
                "formulation": ["Ref"],
                "batch": [1],
                "time": [5],
                "percent_released": [20.0],
            }
        )
        cfg = DissolutionCSVConfig()
        issues = _check_ich_m13b_sd(df, "Ref", cfg)
        assert issues == []

    def test_integration_with_dissolution_study(self) -> None:
        """End-to-end: DissolutionStudy.compare() warns when M13B SD violated."""
        from openpkflow.dissolution.study import DissolutionStudy

        df = pd.DataFrame(
            {
                "formulation": ["Ref", "Ref", "Ref", "Ref", "Ref", "Ref", "Ref", "Ref", "Ref"],
                "batch": [1, 2, 3, 1, 2, 3, 1, 2, 3],
                "time": [5, 5, 5, 15, 15, 15, 30, 30, 30],
                "percent_released": [15.0, 30.0, 45.0, 45.0, 48.0, 46.0, 70.0, 68.0, 72.0],
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
            result = study.compare("Ref", "Test", f2_method="all_points")
            ich_warnings = [x for x in w if "ICH M13B" in str(x.message)]
        assert len(ich_warnings) >= 1
        assert any("ICH M13B" in msg for msg in result.warnings)
