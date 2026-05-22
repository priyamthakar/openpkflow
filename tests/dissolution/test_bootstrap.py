"""Tests for bootstrap_f2.

References:
    Shah VP et al. (1998) Pharm Res, 15(6):889-896. Bootstrap f2 methodology.
"""

import warnings

import numpy as np
import pytest

from openpkflow.dissolution.bootstrap import BootstrapF2Result, bootstrap_f2

# Similar profiles: ref and test very close -> high f2, CI lower bound >= 50
REF_SIMILAR = np.array(
    [
        [20, 40, 60, 75, 88],
        [19, 41, 59, 76, 87],
        [21, 39, 61, 74, 89],
        [20, 40, 60, 75, 88],
        [19, 40, 60, 75, 87],
        [20, 41, 61, 76, 88],
    ],
    dtype=float,
)

TST_SIMILAR = np.array(
    [
        [21, 41, 61, 76, 89],
        [20, 40, 60, 75, 88],
        [22, 42, 62, 77, 90],
        [21, 41, 61, 76, 89],
        [20, 40, 60, 75, 88],
        [21, 41, 61, 76, 89],
    ],
    dtype=float,
)

# Dissimilar profiles: large systematic difference -> low f2
REF_DISSIMILAR = np.array(
    [
        [20, 40, 60, 75, 88],
        [19, 41, 59, 76, 87],
        [21, 39, 61, 74, 89],
    ],
    dtype=float,
)

TST_DISSIMILAR = np.array(
    [
        [5, 15, 28, 42, 60],
        [6, 14, 27, 41, 59],
        [5, 15, 28, 43, 61],
    ],
    dtype=float,
)


class TestBootstrapF2Result:
    def test_is_similar_true(self):
        r = BootstrapF2Result(
            f2_observed=65.0,
            ci_lower=55.0,
            ci_upper=72.0,
            n_replicates=5000,
            confidence_level=0.90,
            n_timepoints=5,
            n_reference_vessels=6,
            n_test_vessels=6,
        )
        assert r.is_similar is True

    def test_is_similar_false(self):
        r = BootstrapF2Result(
            f2_observed=45.0,
            ci_lower=38.0,
            ci_upper=52.0,
            n_replicates=5000,
            confidence_level=0.90,
            n_timepoints=5,
            n_reference_vessels=3,
            n_test_vessels=3,
        )
        assert r.is_similar is False

    def test_is_similar_boundary(self):
        r = BootstrapF2Result(
            f2_observed=55.0,
            ci_lower=50.0,
            ci_upper=60.0,
            n_replicates=5000,
            confidence_level=0.90,
            n_timepoints=5,
            n_reference_vessels=3,
            n_test_vessels=3,
        )
        assert r.is_similar is True

    def test_summary_contains_key_fields(self):
        r = BootstrapF2Result(
            f2_observed=65.0,
            ci_lower=55.0,
            ci_upper=72.0,
            n_replicates=5000,
            confidence_level=0.90,
            n_timepoints=5,
            n_reference_vessels=6,
            n_test_vessels=6,
        )
        s = r.summary()
        assert "65.00" in s
        assert "55.00" in s
        assert "72.00" in s
        assert "SIMILAR" in s


class TestBootstrapF2:
    def test_returns_result_type(self):
        result = bootstrap_f2(REF_SIMILAR, TST_SIMILAR, n_replicates=100, seed=42)
        assert isinstance(result, BootstrapF2Result)

    def test_similar_profiles_ci_lower_above_50(self):
        result = bootstrap_f2(REF_SIMILAR, TST_SIMILAR, n_replicates=2000, seed=42)
        assert result.ci_lower >= 50.0
        assert result.is_similar is True

    def test_dissimilar_profiles_ci_lower_below_50(self):
        result = bootstrap_f2(REF_DISSIMILAR, TST_DISSIMILAR, n_replicates=2000, seed=42)
        assert result.ci_lower < 50.0
        assert result.is_similar is False

    def test_identical_profiles_f2_observed_is_100(self):
        ref = np.array([[20, 40, 60, 80, 90]] * 4, dtype=float)
        result = bootstrap_f2(ref, ref.copy(), n_replicates=100, seed=0)
        assert abs(result.f2_observed - 100.0) < 0.01

    def test_reproducible_with_seed(self):
        r1 = bootstrap_f2(REF_SIMILAR, TST_SIMILAR, n_replicates=500, seed=99)
        r2 = bootstrap_f2(REF_SIMILAR, TST_SIMILAR, n_replicates=500, seed=99)
        assert r1.ci_lower == r2.ci_lower
        assert r1.ci_upper == r2.ci_upper

    def test_different_seeds_different_results(self):
        r1 = bootstrap_f2(REF_SIMILAR, TST_SIMILAR, n_replicates=500, seed=1)
        r2 = bootstrap_f2(REF_SIMILAR, TST_SIMILAR, n_replicates=500, seed=2)
        # Very unlikely to be exactly equal with different seeds
        assert r1.ci_lower != r2.ci_lower or r1.ci_upper != r2.ci_upper

    def test_ci_lower_le_observed_le_upper(self):
        result = bootstrap_f2(REF_SIMILAR, TST_SIMILAR, n_replicates=1000, seed=7)
        assert result.ci_lower <= result.f2_observed <= result.ci_upper

    def test_n_replicates_stored(self):
        result = bootstrap_f2(REF_SIMILAR, TST_SIMILAR, n_replicates=123, seed=0)
        assert result.n_replicates == 123

    def test_confidence_level_stored(self):
        result = bootstrap_f2(
            REF_SIMILAR, TST_SIMILAR, n_replicates=100, confidence_level=0.95, seed=0
        )
        assert result.confidence_level == 0.95

    def test_95_ci_wider_than_90_ci(self):
        r90 = bootstrap_f2(
            REF_SIMILAR, TST_SIMILAR, n_replicates=2000, confidence_level=0.90, seed=42
        )
        r95 = bootstrap_f2(
            REF_SIMILAR, TST_SIMILAR, n_replicates=2000, confidence_level=0.95, seed=42
        )
        width90 = r90.ci_upper - r90.ci_lower
        width95 = r95.ci_upper - r95.ci_lower
        assert width95 >= width90

    def test_error_1d_reference(self):
        with pytest.raises(ValueError, match="2-D array"):
            bootstrap_f2(np.array([20, 40, 60]), TST_SIMILAR)

    def test_error_1d_test(self):
        with pytest.raises(ValueError, match="2-D array"):
            bootstrap_f2(REF_SIMILAR, np.array([20, 40, 60]))

    def test_error_mismatched_timepoints(self):
        ref = np.ones((3, 5))
        tst = np.ones((3, 6))
        with pytest.raises(ValueError, match="timepoints"):
            bootstrap_f2(ref, tst)

    def test_error_too_few_timepoints(self):
        ref = np.ones((3, 2))
        tst = np.ones((3, 2))
        with pytest.raises(ValueError, match="3 timepoints"):
            bootstrap_f2(ref, tst)

    def test_error_too_few_vessels(self):
        ref = np.ones((1, 5))
        tst = np.ones((3, 5))
        with pytest.raises(ValueError, match="2 reference vessels"):
            bootstrap_f2(ref, tst)

    def test_warns_large_sample(self):
        big = np.ones((12, 5))
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            bootstrap_f2(big, big.copy(), n_replicates=10, seed=0)
            assert any("Bootstrap f2" in str(warning.message) for warning in w)

    def test_metadata_stored(self):
        result = bootstrap_f2(REF_SIMILAR, TST_SIMILAR, n_replicates=100, seed=0)
        assert result.n_timepoints == 5
        assert result.n_reference_vessels == 6
        assert result.n_test_vessels == 6
