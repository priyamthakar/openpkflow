"""Tests for SUPAC-IR screening and alcohol dose-dumping helpers.

References
----------
FDA Guidance for Industry: Immediate Release Solid Oral Dosage Forms:
Scale-Up and Postapproval Changes (SUPAC-IR, 1995). CDER.

FDA Guidance for Industry: Dissolution Testing of Immediate Release Solid
Oral Dosage Forms (1997). CDER.
"""

from __future__ import annotations

import math

import pytest

from openpkflow.dissolution import (
    AlcoholDoseDumpingResult,
    SupacClassification,
    alcohol_dose_dumping_assessment,
    classify_supac_ir_level,
)
from openpkflow.dissolution.similarity import f2


class TestClassifySupacIrLevel:
    """Tests for classify_supac_ir_level."""

    def test_zero_change_is_level_1(self) -> None:
        """Degenerate: zero change is always Level 1.

        Reference: by definition of Level 1 (small / no composition change);
        FDA SUPAC-IR (1995) Level 1 band includes the zero-change case.
        """
        for cat in ("non_critical", "critical"):
            result = classify_supac_ir_level(0.0, cat)  # type: ignore[arg-type]
            assert isinstance(result, SupacClassification)
            assert result.level == 1
            assert result.change_pct == 0.0
            assert result.component_category == cat
            assert len(result.recommended_tests) >= 1

    def test_non_critical_filler_bands_supac_ir(self) -> None:
        """Non-critical (filler-like) Level 1/2/3 bands match documented table.

        Reference
        ---------
        FDA SUPAC-IR (1995): Level 1 filler change up to +/-5% of total
        formulation weight; moderate (Level 2) composition changes are
        larger than Level 1 and below the Level 3 (large) band. Screening
        table in openpkflow: L1 <= 5%, L2 <= 10%, else L3.
        """
        r1 = classify_supac_ir_level(5.0, "non_critical")
        assert r1.level == 1
        r2 = classify_supac_ir_level(5.01, "non_critical")
        assert r2.level == 2
        r2b = classify_supac_ir_level(10.0, "non_critical")
        assert r2b.level == 2
        r3 = classify_supac_ir_level(10.01, "non_critical")
        assert r3.level == 3
        assert "Level 3" in r3.rationale
        assert any("bioequivalence" in t.lower() for t in r3.recommended_tests)

    def test_critical_tighter_thresholds(self) -> None:
        """Critical (functional) excipients use tighter L1/L2 bands.

        Reference
        ---------
        FDA SUPAC-IR (1995) assigns narrower percent bands to binders,
        disintegrants, and lubricants than to fillers. Screening collapse:
        L1 <= 1%, L2 <= 2.5%, else L3.
        """
        assert classify_supac_ir_level(1.0, "critical").level == 1
        assert classify_supac_ir_level(1.01, "critical").level == 2
        assert classify_supac_ir_level(2.5, "critical").level == 2
        assert classify_supac_ir_level(2.51, "critical").level == 3

    def test_frozen_dataclass(self) -> None:
        result = classify_supac_ir_level(3.0, "non_critical")
        with pytest.raises(AttributeError):
            result.level = 2  # type: ignore[misc]

    def test_negative_change_raises(self) -> None:
        with pytest.raises(ValueError, match="change_pct must be >= 0"):
            classify_supac_ir_level(-1.0, "non_critical")

    def test_invalid_category_raises(self) -> None:
        with pytest.raises(ValueError, match="component_category"):
            classify_supac_ir_level(1.0, "binder")  # type: ignore[arg-type]


class TestAlcoholDoseDumping:
    """Tests for alcohol_dose_dumping_assessment."""

    def test_identical_profiles_pass_f2_100(self) -> None:
        """Degenerate: identical control and ethanol profiles yield f2 = 100.

        Reference: f2 = 100 when profiles are identical (FDA 1997 dissolution
        guidance; by definition of the f2 formula).
        """
        control = [10.0, 30.0, 50.0, 70.0, 90.0]
        eth = {5.0: list(control), 20.0: list(control), 40.0: list(control)}
        times = [5.0, 10.0, 15.0, 30.0, 45.0]
        result = alcohol_dose_dumping_assessment(control, eth, times)
        assert isinstance(result, AlcoholDoseDumpingResult)
        assert result.overall_pass is True
        for v in result.f2_by_ethanol_pct.values():
            assert math.isclose(v, 100.0, abs_tol=1e-9)

    def test_divergent_ethanol_fails_threshold(self) -> None:
        """Large ethanol-driven release increase fails f2 >= 50.

        Reference
        ---------
        FDA 1997 dissolution guidance: f2 < 50 indicates profiles are not
        similar (approximately >10 percentage-point average difference).
        Alcohol media that accelerate release relative to aqueous control
        are screened as potential dose-dumping signals.
        """
        control = [10.0, 25.0, 40.0, 55.0, 70.0]
        # ~25 percentage points higher at each time -> f2 well below 50
        eth_fast = [35.0, 50.0, 65.0, 80.0, 95.0]
        eth = {40.0: eth_fast}
        result = alcohol_dose_dumping_assessment(control, eth, f2_threshold=50.0)
        assert result.overall_pass is False
        assert result.f2_by_ethanol_pct[40.0] < 50.0
        # Cross-check against public f2 helper
        assert math.isclose(
            result.f2_by_ethanol_pct[40.0],
            f2(control, eth_fast),
            rel_tol=1e-12,
        )

    def test_mixed_ethanol_levels(self) -> None:
        control = [15.0, 35.0, 55.0, 75.0, 90.0]
        similar = [16.0, 34.0, 56.0, 74.0, 91.0]
        different = [40.0, 60.0, 80.0, 95.0, 100.0]
        result = alcohol_dose_dumping_assessment(
            control,
            {5.0: similar, 40.0: different},
            time_points=[10, 20, 30, 45, 60],
        )
        assert result.f2_by_ethanol_pct[5.0] >= 50.0
        assert result.f2_by_ethanol_pct[40.0] < 50.0
        assert result.overall_pass is False

    def test_empty_ethanol_map_raises(self) -> None:
        with pytest.raises(ValueError, match="at least one"):
            alcohol_dose_dumping_assessment([10, 20, 30], {})

    def test_length_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="length"):
            alcohol_dose_dumping_assessment(
                [10, 20, 30, 40, 50],
                {5.0: [10, 20, 30]},
            )
