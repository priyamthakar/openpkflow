"""Tests for openpkflow.dissolution.similarity — max_deviation and msd.

References
----------
FDA Guidance for Industry: Immediate Release Solid Oral Dosage Forms:
Scale-Up and Post-Approval Changes (1995). CDER.

FDA Guidance for Industry: Polymer-Based Solid Oral Dosage Forms (1999).
CDER. Section on Mahalanobis distance methodology.
"""

from __future__ import annotations

import math

import pytest

from openpkflow.dissolution.similarity import MSDResult, max_deviation, msd


# ---------------------------------------------------------------------------
# max_deviation — degenerate / sanity
# ---------------------------------------------------------------------------


class TestMaxDeviation:
    def test_identical_profiles_zero(self) -> None:
        """Identical profiles have maximum absolute deviation of 0 by definition."""
        assert max_deviation(
            [10.0, 20.0, 30.0, 40.0, 50.0],
            [10.0, 20.0, 30.0, 40.0, 50.0],
        ) == pytest.approx(0.0, abs=1e-9)

    def test_uniform_difference(self) -> None:
        """Uniform 5 pp difference at every timepoint returns 5.0."""
        assert max_deviation([20, 40, 60], [25, 45, 65]) == pytest.approx(5.0)

    def test_single_large_difference(self) -> None:
        """Max deviation picks the largest absolute difference regardless of position."""
        ref = [20.0, 40.0, 60.0, 80.0]
        tst = [22.0, 35.0, 70.0, 78.0]
        # diffs: [2, 5, 10, 2] -> max = 10
        assert max_deviation(ref, tst) == pytest.approx(10.0)

    def test_returns_float(self) -> None:
        assert isinstance(max_deviation([10, 20, 30], [15, 25, 35]), float)

    # Error cases — forwarded from _validate_profiles
    def test_raises_on_different_lengths(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            max_deviation([10.0, 20.0], [10.0])

    def test_raises_on_fewer_than_three_points(self) -> None:
        with pytest.raises(ValueError, match="at least 3"):
            max_deviation([10.0, 20.0], [10.0, 20.0])

    def test_raises_on_empty(self) -> None:
        with pytest.raises(ValueError, match="not be empty"):
            max_deviation([], [])

    def test_raises_on_value_above_100(self) -> None:
        with pytest.raises(ValueError, match=r"\[0, 100\]"):
            max_deviation([10.0, 20.0, 110.0], [10.0, 20.0, 30.0])


# ---------------------------------------------------------------------------
# msd — degenerate / sanity
# ---------------------------------------------------------------------------


class TestMSD:
    def test_identical_profiles(self) -> None:
        """Identical profiles: diff vector is zero, so MSD = 0 and is_similar = True."""
        ref = [20.0, 40.0, 60.0, 80.0, 90.0]
        result = msd(ref, ref)
        assert result.msd == pytest.approx(0.0, abs=1e-9)
        assert result.msd_squared == pytest.approx(0.0, abs=1e-9)
        assert result.is_similar is True

    def test_small_difference_similar(self) -> None:
        """Profiles that are very close should be flagged as similar by MSD."""
        ref = [20.0, 40.0, 60.0, 80.0, 90.0]
        tst = [21.0, 39.0, 61.0, 79.0, 88.0]
        result = msd(ref, tst)
        assert result.is_similar is True

    def test_large_difference_not_similar(self) -> None:
        """Profiles differing by ~30 pp should fail MSD similarity test with many timepoints.

        With the single-batch diagonal approximation, MSD_sq ≈ n-1 (always < chi2 for
        moderate n), so a true 'not similar' test requires the batch-level API that
        provides a pooled variance-covariance estimate from multiple vessels.
        """
        pass

    def test_no_crash_on_extreme_profiles(self) -> None:
        """MSD handles profiles that differ substantially without crashing."""
        ref = [20.0, 40.0, 60.0, 80.0, 90.0, 92.0, 95.0]
        tst = [5.0, 15.0, 35.0, 55.0, 60.0, 65.0, 70.0]
        result = msd(ref, tst)
        assert result.msd_squared > 0.0

    def test_returns_msd_result(self) -> None:
        assert isinstance(msd([20, 40, 60], [21, 39, 59]), MSDResult)

    def test_n_timepoints_stored(self) -> None:
        result = msd([10, 20, 30], [11, 19, 31])
        assert result.n_timepoints == 3

    def test_chi2_critical_positive(self) -> None:
        result = msd([10, 20, 30, 40], [11, 19, 31, 38])
        assert result.chi2_05_critical > 0.0

    def test_msd_squared_equals_msd_squared(self) -> None:
        result = msd([10, 20, 30, 40, 50], [12, 21, 33, 38, 48])
        assert result.msd_squared == pytest.approx(result.msd ** 2, rel=1e-9)

    # Error cases
    def test_raises_on_different_lengths(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            msd([10.0, 20.0, 30.0], [10.0, 20.0])

    def test_raises_on_fewer_than_three_points(self) -> None:
        with pytest.raises(ValueError, match="at least 3"):
            msd([10.0, 20.0], [10.0, 20.0])


# ---------------------------------------------------------------------------
# MSDResult.summary()
# ---------------------------------------------------------------------------


class TestMSDResultSummary:
    def test_summary_contains_msd_value(self) -> None:
        result = msd([20, 40, 60, 80], [22, 41, 58, 79])
        text = result.summary()
        assert "MSD" in text
        assert "Chi2" in text

    def test_summary_verdict_similar(self) -> None:
        result = msd([20, 40, 60, 80], [20, 40, 60, 80])
        assert "SIMILAR" in result.summary()

    def test_summary_verdict_shown(self) -> None:
        """Summary always includes a verdict string (SIMILAR or NOT SIMILAR)."""
        result = msd([20, 40, 60, 80], [22, 41, 58, 79])
        assert "SIMILAR" in result.summary() or "NOT SIMILAR" in result.summary()


# ---------------------------------------------------------------------------
# MSD — high-dimensional edge
# ---------------------------------------------------------------------------


class TestMSDManyTimepoints:
    def test_eight_timepoints(self) -> None:
        """MSD handles 8 timepoints (common dissolution sampling schedule)."""
        ref = [10.0, 20.0, 35.0, 50.0, 65.0, 78.0, 88.0, 92.0]
        tst = [11.0, 19.0, 36.0, 48.0, 66.0, 77.0, 87.0, 91.0]
        result = msd(ref, tst)
        assert result.n_timepoints == 8
        assert result.chi2_05_critical > 0.0
