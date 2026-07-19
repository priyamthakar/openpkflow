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
    """Tests for classify_supac_ir_level with function-specific tables."""

    def test_zero_change_is_level_1(self) -> None:
        """Degenerate: zero change is always Level 1."""
        for cat in ("filler", "binder", "glidant"):
            result = classify_supac_ir_level(0.0, cat)
            assert isinstance(result, SupacClassification)
            assert result.level == 1
            assert result.change_pct == 0.0
            assert result.component_category == cat
            assert len(result.recommended_tests) >= 1

    def test_filler_bands_supac_ir(self) -> None:
        """Filler Level 1/2/3 bands match SUPAC-IR table (5% / 10%).

        Reference: FDA SUPAC-IR (1995) diluent/filler composition changes.
        """
        assert classify_supac_ir_level(5.0, "filler").level == 1
        assert classify_supac_ir_level(5.01, "filler").level == 2
        assert classify_supac_ir_level(10.0, "filler").level == 2
        assert classify_supac_ir_level(10.01, "filler").level == 3

    def test_binder_tighter_than_filler(self) -> None:
        """Binder L1 is 0.5% (much tighter than filler 5%).

        Reference: FDA SUPAC-IR (1995) binder table.
        """
        assert classify_supac_ir_level(0.5, "binder").level == 1
        assert classify_supac_ir_level(0.51, "binder").level == 2
        assert classify_supac_ir_level(1.0, "binder").level == 2
        assert classify_supac_ir_level(1.01, "binder").level == 3

    def test_stearate_tighter_than_other_lubricant(self) -> None:
        """Mg/Ca stearate L1 is 0.25%; other lubricants L1 is 1%.

        Reference: FDA SUPAC-IR (1995) lubricant tables.
        """
        assert classify_supac_ir_level(0.25, "lubricant_stearate").level == 1
        assert classify_supac_ir_level(0.26, "lubricant_stearate").level == 2
        assert classify_supac_ir_level(1.0, "lubricant_other").level == 1
        assert classify_supac_ir_level(1.01, "lubricant_other").level == 2

    def test_disintegrant_starch_vs_other(self) -> None:
        """Starch disintegrant L1=3%; other disintegrant L1=1%."""
        assert classify_supac_ir_level(3.0, "disintegrant_starch").level == 1
        assert classify_supac_ir_level(3.01, "disintegrant_starch").level == 2
        assert classify_supac_ir_level(1.0, "disintegrant_other").level == 1
        assert classify_supac_ir_level(1.01, "disintegrant_other").level == 2

    def test_glidant_and_film_coat(self) -> None:
        assert classify_supac_ir_level(1.0, "glidant").level == 1
        assert classify_supac_ir_level(2.0, "glidant").level == 2
        assert classify_supac_ir_level(2.01, "film_coat").level == 3

    def test_deprecated_aliases_still_work(self) -> None:
        r = classify_supac_ir_level(5.0, "non_critical")
        assert r.level == 1
        assert "deprecated" in r.rationale.lower() or "alias" in r.rationale.lower()

    def test_frozen_dataclass(self) -> None:
        result = classify_supac_ir_level(3.0, "filler")
        with pytest.raises(AttributeError):
            result.level = 2  # type: ignore[misc]

    def test_negative_change_raises(self) -> None:
        with pytest.raises(ValueError, match="change_pct must be >= 0"):
            classify_supac_ir_level(-1.0, "filler")

    def test_invalid_category_raises(self) -> None:
        with pytest.raises(ValueError, match="component_category"):
            classify_supac_ir_level(1.0, "not_a_real_class")


class TestAlcoholDoseDumping:
    """Tests for alcohol_dose_dumping_assessment."""

    def test_identical_profiles_pass_f2_100(self) -> None:
        """Degenerate: identical control and ethanol profiles yield f2 = 100."""
        control = [10.0, 30.0, 50.0, 70.0, 90.0]
        eth = {5.0: list(control), 20.0: list(control), 40.0: list(control)}
        times = [5.0, 10.0, 15.0, 30.0, 45.0]
        result = alcohol_dose_dumping_assessment(control, eth, times)
        assert isinstance(result, AlcoholDoseDumpingResult)
        assert result.overall_pass is True
        for v in result.f2_by_ethanol_pct.values():
            assert math.isclose(v, 100.0, abs_tol=1e-9)

    def test_divergent_ethanol_fails_threshold(self) -> None:
        """Large ethanol-driven release increase fails f2 >= 50."""
        control = [10.0, 25.0, 40.0, 55.0, 70.0]
        eth_fast = [35.0, 50.0, 65.0, 80.0, 95.0]
        eth = {40.0: eth_fast}
        result = alcohol_dose_dumping_assessment(control, eth, f2_threshold=50.0)
        assert result.overall_pass is False
        assert result.f2_by_ethanol_pct[40.0] < 50.0
        assert math.isclose(
            result.f2_by_ethanol_pct[40.0],
            f2(control, eth_fast, method="regulatory"),
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

    def test_time_points_must_be_strictly_increasing(self) -> None:
        with pytest.raises(ValueError, match="strictly increasing"):
            alcohol_dose_dumping_assessment(
                [10, 20, 30],
                {5.0: [10, 20, 30]},
                time_points=[5, 5, 15],
            )

    def test_regulatory_f2_trims_extra_plateau_points(self) -> None:
        control = [20, 60, 86, 90, 95]
        ethanol = [20, 60, 86, 100, 100]
        result = alcohol_dose_dumping_assessment(
            control,
            {20.0: ethanol},
            time_points=[5, 10, 15, 20, 30],
        )
        assert result.f2_by_ethanol_pct[20.0] == pytest.approx(
            f2(control, ethanol, method="regulatory")
        )
