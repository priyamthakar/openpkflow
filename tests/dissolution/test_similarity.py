"""Tests for openpkflow.dissolution.similarity (f1 and f2)."""

from __future__ import annotations

import math

import pytest

from openpkflow.dissolution.similarity import f1, f2


# ---------------------------------------------------------------------------
# Degenerate / sanity cases
# ---------------------------------------------------------------------------


def test_f2_identical_profiles_is_100() -> None:
    """f2 of identical profiles equals 100 by definition (zero squared differences)."""
    assert f2([10.0, 20.0, 30.0, 40.0, 50.0], [10.0, 20.0, 30.0, 40.0, 50.0]) == pytest.approx(
        100.0, abs=1e-9
    )


def test_f1_identical_profiles_is_zero() -> None:
    """f1 of identical profiles equals 0 by definition (zero absolute differences)."""
    assert f1([10.0, 20.0, 30.0, 40.0, 50.0], [10.0, 20.0, 30.0, 40.0, 50.0]) == pytest.approx(
        0.0, abs=1e-9
    )


# ---------------------------------------------------------------------------
# Reference validation cases (FDA 1997)
# ---------------------------------------------------------------------------


def test_f2_ten_percent_difference_near_50() -> None:
    """f2 ≈ 50 when profiles differ by 10 pp at every timepoint (FDA similarity threshold).

    Manual calculation:
        R = [40, 60, 80, 90, 95], T = [30, 50, 70, 80, 85]
        differences: all -10, so sum of squares = 5 * 100 = 500
        mean squared diff = 500 / 5 = 100
        f2 = 50 * log10(100 / sqrt(1 + 100))
           = 50 * log10(100 / sqrt(101))
           = 50 * log10(100 / 10.0499...)
           = 50 * log10(9.9504...)
           = 50 * 0.99785...
           ≈ 49.89

    Reference
    ---------
    FDA Guidance for Industry: Dissolution Testing of Immediate Release
    Solid Oral Dosage Forms (1997). CDER, U.S. Food and Drug Administration.
    """
    R = [40.0, 60.0, 80.0, 90.0, 95.0]
    T = [30.0, 50.0, 70.0, 80.0, 85.0]
    result = f2(R, T)
    assert result == pytest.approx(50.0, abs=2.0), (
        f"Expected f2 ≈ 50 (±2) for a 10 pp uniform difference; got {result:.4f}"
    )


def test_f1_ten_percent_reduction_is_exact() -> None:
    """f1 = 10.0 exactly when test is a uniform 10% reduction of reference.

    Manual calculation:
        R = [40, 60, 80], T = [36, 54, 72]  (each T = 0.9 * R)
        |R-T|: [4, 6, 8]   sum = 18
        sum(R): 180
        f1 = 18 / 180 * 100 = 10.0

    Reference
    ---------
    FDA Guidance for Industry: Dissolution Testing of Immediate Release
    Solid Oral Dosage Forms (1997). CDER, U.S. Food and Drug Administration.
    """
    R = [40.0, 60.0, 80.0]
    T = [36.0, 54.0, 72.0]
    assert f1(R, T) == pytest.approx(10.0, abs=1e-9)


# ---------------------------------------------------------------------------
# Symmetry / consistency
# ---------------------------------------------------------------------------


def test_f2_symmetric_for_identical_profiles() -> None:
    """f2(R, T) == f2(T, R) for identical profiles; documents that f2 is symmetric in general.

    f2 uses squared differences (Rt - Tt)², which are symmetric, so f2(R,T) == f2(T,R)
    for any profiles mathematically.  f1 is NOT symmetric because it divides by sum(R).
    This test verifies the symmetric property on the identical-profile degenerate case.
    """
    R = [10.0, 20.0, 30.0, 40.0, 50.0]
    assert f2(R, R) == pytest.approx(f2(R, R), abs=1e-12)


# ---------------------------------------------------------------------------
# Error cases — length / size validation
# ---------------------------------------------------------------------------


def test_f2_raises_on_different_lengths() -> None:
    """f2 raises ValueError when reference and test have different lengths."""
    with pytest.raises(ValueError, match="same length"):
        f2([10.0, 20.0, 30.0], [10.0, 20.0])


def test_f1_raises_on_different_lengths() -> None:
    """f1 raises ValueError when reference and test have different lengths."""
    with pytest.raises(ValueError, match="same length"):
        f1([10.0, 20.0, 30.0], [10.0, 20.0])


def test_f2_raises_on_empty_arrays() -> None:
    """f2 raises ValueError when empty arrays are supplied."""
    with pytest.raises(ValueError, match="not be empty"):
        f2([], [])


def test_f1_raises_on_empty_arrays() -> None:
    """f1 raises ValueError when empty arrays are supplied."""
    with pytest.raises(ValueError, match="not be empty"):
        f1([], [])


def test_f2_raises_on_one_element() -> None:
    """f2 raises ValueError for a single-timepoint array (min_points=3 required)."""
    with pytest.raises(ValueError, match="at least 3"):
        f2([50.0], [50.0])


def test_f2_raises_on_two_elements() -> None:
    """f2 raises ValueError for a two-timepoint array (min_points=3 required)."""
    with pytest.raises(ValueError, match="at least 3"):
        f2([10.0, 50.0], [10.0, 50.0])


def test_f1_raises_on_one_element() -> None:
    """f1 raises ValueError for a single-timepoint array (min_points=3 required)."""
    with pytest.raises(ValueError, match="at least 3"):
        f1([50.0], [50.0])


def test_f1_raises_on_two_elements() -> None:
    """f1 raises ValueError for a two-timepoint array (min_points=3 required)."""
    with pytest.raises(ValueError, match="at least 3"):
        f1([10.0, 50.0], [10.0, 50.0])


# ---------------------------------------------------------------------------
# Error cases — value range / NaN / inf
# ---------------------------------------------------------------------------


def test_f2_raises_on_value_above_100() -> None:
    """f2 raises ValueError when a value exceeds 100 (not a valid percent released)."""
    with pytest.raises(ValueError, match=r"\[0, 100\]"):
        f2([10.0, 20.0, 101.0], [10.0, 20.0, 30.0])


def test_f2_raises_on_negative_value() -> None:
    """f2 raises ValueError when a value is negative (not a valid percent released)."""
    with pytest.raises(ValueError, match=r"\[0, 100\]"):
        f2([-1.0, 20.0, 30.0], [10.0, 20.0, 30.0])


def test_f2_raises_on_nan() -> None:
    """f2 raises ValueError when a NaN value is present in either array."""
    with pytest.raises(ValueError, match="not finite"):
        f2([10.0, float("nan"), 30.0], [10.0, 20.0, 30.0])


def test_f2_raises_on_inf() -> None:
    """f2 raises ValueError when an infinite value is present in either array."""
    with pytest.raises(ValueError, match="not finite"):
        f2([10.0, 20.0, 30.0], [10.0, float("inf"), 30.0])


def test_f1_raises_on_nan() -> None:
    """f1 raises ValueError when a NaN value is present in either array."""
    with pytest.raises(ValueError, match="not finite"):
        f1([10.0, float("nan"), 30.0], [10.0, 20.0, 30.0])


# ---------------------------------------------------------------------------
# Error cases — f1-specific
# ---------------------------------------------------------------------------


def test_f1_raises_on_zero_reference_sum() -> None:
    """f1 raises ValueError when all reference values are zero (division by zero)."""
    with pytest.raises(ValueError, match="Sum of reference values is zero"):
        f1([0.0, 0.0, 0.0], [10.0, 20.0, 30.0])


# ---------------------------------------------------------------------------
# Acceptance of valid edge-value inputs
# ---------------------------------------------------------------------------


def test_f2_accepts_boundary_values_0_and_100() -> None:
    """f2 accepts values exactly at the boundaries 0 and 100 (inclusive range)."""
    result = f2([0.0, 50.0, 100.0], [0.0, 50.0, 100.0])
    assert result == pytest.approx(100.0, abs=1e-9)


def test_f2_accepts_sequence_types() -> None:
    """f2 accepts tuples, lists, and other Sequence types without error."""
    assert f2((10.0, 20.0, 30.0), (10.0, 20.0, 30.0)) == pytest.approx(100.0, abs=1e-9)


def test_f1_accepts_sequence_types() -> None:
    """f1 accepts tuples, lists, and other Sequence types without error."""
    assert f1((10.0, 20.0, 30.0), (10.0, 20.0, 30.0)) == pytest.approx(0.0, abs=1e-9)


# ---------------------------------------------------------------------------
# Return-value sanity (f2 range)
# ---------------------------------------------------------------------------


def test_f2_returns_float() -> None:
    """f2 always returns a Python float, not an int or numpy scalar."""
    result = f2([10.0, 50.0, 90.0], [10.0, 50.0, 90.0])
    assert isinstance(result, float)


def test_f1_returns_float() -> None:
    """f1 always returns a Python float, not an int or numpy scalar."""
    result = f1([10.0, 50.0, 90.0], [10.0, 50.0, 90.0])
    assert isinstance(result, float)


def test_f2_decreases_as_profiles_diverge() -> None:
    """f2 decreases monotonically as the magnitude of profile differences increases."""
    R = [40.0, 60.0, 80.0, 90.0, 95.0]
    T_close = [38.0, 58.0, 78.0, 88.0, 93.0]
    T_far = [20.0, 40.0, 60.0, 70.0, 75.0]
    assert f2(R, T_close) > f2(R, T_far)
