"""Tests for openpkflow.be.methods -- TOST bioequivalence math.

Reference
---------
Schuirmann D.J. (1987). A comparison of the Two One-Sided Tests Procedure
and the Power Approach for assessing the equivalence of average bioavailability.
J Pharmacokinet Biopharm 15(6):657-680. DOI: 10.1007/BF01068419

FDA (2003). Guidance for Industry: Bioavailability and Bioequivalence Studies
for Orally Administered Drug Products -- General Considerations.
https://www.fda.gov/media/71513/download
"""

from __future__ import annotations

import math

import pytest

from openpkflow.be.methods import be_tost


class TestBETOSTDegenerate:
    def test_identical_gives_gmr_one(self) -> None:
        """T == R -> GMR = 1.0 by definition. Degenerate TOST case."""
        ref = [100.0, 100.0, 100.0, 100.0, 100.0, 100.0]
        tst = [100.0, 100.0, 100.0, 100.0, 100.0, 100.0]
        result = be_tost(ref, tst)
        assert result.gmr == pytest.approx(1.0, abs=1e-10)
        assert result.bioequivalent is True

    def test_identical_ci_is_point(self) -> None:
        """T == R with no variability gives a degenerate CI at GMR = 1.0."""
        ref = [80.0, 100.0, 120.0]
        tst = [80.0, 100.0, 120.0]
        result = be_tost(ref, tst)
        assert result.gmr_lower_90ci == pytest.approx(1.0, abs=1e-9)
        assert result.gmr_upper_90ci == pytest.approx(1.0, abs=1e-9)

    def test_constant_ratio_090_is_be(self) -> None:
        """Constant T/R = 0.90 across all subjects: GMR = 0.90, CI = [0.90, 0.90].

        With zero variance the 90% CI collapses to the point GMR = 0.90,
        which is within [0.80, 1.25].
        """
        ref = [100.0, 120.0, 80.0, 110.0, 90.0, 95.0]
        tst = [r * 0.90 for r in ref]
        result = be_tost(ref, tst)
        assert result.gmr == pytest.approx(0.90, abs=1e-9)
        assert result.gmr_lower_90ci == pytest.approx(0.90, abs=1e-9)
        assert result.gmr_upper_90ci == pytest.approx(0.90, abs=1e-9)
        assert result.bioequivalent is True

    def test_constant_ratio_070_is_not_be(self) -> None:
        """Constant T/R = 0.70: GMR = 0.70, outside [0.80, 1.25].

        Reference: FDA 80-125% acceptance window -- 0.70 is below the lower limit.
        """
        ref = [100.0] * 6
        tst = [70.0] * 6
        result = be_tost(ref, tst)
        assert result.gmr == pytest.approx(0.70, abs=1e-9)
        assert result.bioequivalent is False

    def test_constant_ratio_140_is_not_be(self) -> None:
        """Constant T/R = 1.40: GMR = 1.40, above 1.25 upper limit."""
        ref = [100.0] * 4
        tst = [140.0] * 4
        result = be_tost(ref, tst)
        assert result.gmr == pytest.approx(1.40, abs=1e-9)
        assert result.bioequivalent is False


class TestBETOSTKnownCI:
    def test_known_ci_width_n4(self) -> None:
        """Verify 90% CI bounds against manual calculation for n=4.

        Design: log-differences = [0, 0, 0.2, -0.2]
        - d_bar = 0  -> GMR = 1.0
        - s_d = sqrt((0+0+0.04+0.04) / 3) = sqrt(0.0267) = 0.16330
        - SE = 0.16330 / sqrt(4) = 0.08165
        - t(0.05, 3) = 2.3534
        - half-width = 2.3534 * 0.08165 = 0.19222
        - 90% CI = [exp(-0.19222), exp(0.19222)] = [0.8250, 1.2120]

        Reference: Schuirmann (1987) eq. for paired two one-sided tests.
        """
        ref = [100.0, 100.0, 100.0, 100.0]
        tst = [100.0, 100.0, math.exp(0.2) * 100.0, math.exp(-0.2) * 100.0]
        result = be_tost(ref, tst)
        assert result.gmr == pytest.approx(1.0, abs=1e-9)
        assert result.gmr_lower_90ci == pytest.approx(0.8250, abs=0.001)
        assert result.gmr_upper_90ci == pytest.approx(1.2120, abs=0.001)
        assert result.bioequivalent is True

    def test_gmr_offset_with_variability(self) -> None:
        """Non-unity GMR with variability: CI should be asymmetric about the limits.

        d_bar = log(0.90) = -0.10536
        With log_diffs = [-0.10536, -0.10536, -0.10536 + 0.10, -0.10536 - 0.10]
        GMR should be exp(-0.10536) = 0.90.
        """
        delta = math.log(0.90)
        ref = [100.0, 100.0, 100.0, 100.0]
        tst = [
            math.exp(delta) * 100.0,
            math.exp(delta) * 100.0,
            math.exp(delta + 0.10) * 100.0,
            math.exp(delta - 0.10) * 100.0,
        ]
        result = be_tost(ref, tst)
        assert result.gmr == pytest.approx(0.90, abs=1e-9)
        # CI lower must be below 0.90, CI upper must be above 0.90
        assert result.gmr_lower_90ci < result.gmr
        assert result.gmr_upper_90ci > result.gmr


class TestBETOSTCVIntra:
    def test_zero_variability_gives_zero_cv(self) -> None:
        """No within-subject variability -> intra-subject CV = 0."""
        ref = [100.0, 100.0, 100.0]
        tst = [90.0, 90.0, 90.0]
        result = be_tost(ref, tst)
        assert result.cv_intra_pct == pytest.approx(0.0, abs=1e-9)

    def test_cv_intra_positive_with_variability(self) -> None:
        """Non-zero variability -> CV > 0."""
        ref = [100.0, 100.0, 100.0, 100.0]
        tst = [90.0, 100.0, 110.0, 95.0]
        result = be_tost(ref, tst)
        assert result.cv_intra_pct > 0.0


class TestBETOSTNTILimits:
    def test_nti_limits_stricter(self) -> None:
        """GMR = 0.88 passes standard 80-125% but fails NTI 90-111.11%.

        NTI products use narrower acceptance limits per EMA guidance.
        Caller sets be_lower=0.90, be_upper=1.1111.
        0.88 >= 0.80 (passes standard lower) but 0.88 < 0.90 (fails NTI lower).
        """
        ref = [100.0] * 6
        tst = [88.0] * 6
        standard = be_tost(ref, tst, be_lower=0.80, be_upper=1.25)
        nti = be_tost(ref, tst, be_lower=0.90, be_upper=1.1111)
        assert standard.bioequivalent is True
        assert nti.bioequivalent is False


class TestBETOSTValidation:
    def test_mismatched_lengths_raises(self) -> None:
        """Mismatched reference/test lengths must raise ValueError."""
        with pytest.raises(ValueError, match="same length"):
            be_tost([1.0, 2.0], [1.0])

    def test_fewer_than_two_subjects_raises(self) -> None:
        """Single subject must raise ValueError."""
        with pytest.raises(ValueError, match="at least 2"):
            be_tost([100.0], [95.0])

    def test_nonpositive_reference_raises(self) -> None:
        """Zero or negative reference value must raise ValueError."""
        with pytest.raises(ValueError, match="positive"):
            be_tost([100.0, 0.0], [100.0, 95.0])

    def test_nonpositive_test_raises(self) -> None:
        """Zero or negative test value must raise ValueError."""
        with pytest.raises(ValueError, match="positive"):
            be_tost([100.0, 100.0], [95.0, -5.0])

    def test_invalid_limits_raises(self) -> None:
        """be_lower >= be_upper must raise ValueError."""
        with pytest.raises(ValueError, match="be_lower"):
            be_tost([100.0, 100.0], [90.0, 90.0], be_lower=1.25, be_upper=0.80)

    def test_log_diffs_length_matches_n(self) -> None:
        """log_diffs list should have n entries."""
        ref = [100.0, 110.0, 90.0]
        tst = [95.0, 105.0, 88.0]
        result = be_tost(ref, tst)
        assert len(result.log_diffs) == 3

    def test_symmetry_of_gmr(self) -> None:
        """Swapping T and R inverts GMR: GMR(T,R) = 1 / GMR(R,T)."""
        ref = [100.0, 120.0, 80.0, 110.0]
        tst = [95.0, 115.0, 82.0, 108.0]
        r1 = be_tost(ref, tst)
        r2 = be_tost(tst, ref)
        assert r1.gmr * r2.gmr == pytest.approx(1.0, abs=1e-9)
