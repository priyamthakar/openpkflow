"""Property-based tests for bootstrap f2 invariants."""

from __future__ import annotations

import numpy as np
from hypothesis import given
from hypothesis import strategies as st

from openpkflow.dissolution.bootstrap import bootstrap_f2


class TestBootstrapF2:
    @given(
        st.integers(min_value=2, max_value=5),
        st.integers(min_value=3, max_value=6),
    )
    def test_ci_lower_not_greater_than_ci_upper(self, n_vessels, n_timepoints):
        n_vessels = max(2, n_vessels)
        n_timepoints = max(3, n_timepoints)
        np.random.seed(42)
        ref = np.random.uniform(30, 100, (n_vessels, n_timepoints))
        tst = ref + ref * 0.05 * np.random.randn(n_vessels, n_timepoints)
        tst = np.clip(tst, 0, 100)

        result = bootstrap_f2(ref, tst, n_replicates=200, seed=42)
        assert result.ci_lower <= result.ci_upper

    @given(
        st.integers(min_value=2, max_value=5),
        st.integers(min_value=3, max_value=5),
    )
    def test_seed_reproducibility(self, n_vessels, n_timepoints):
        n_vessels = max(2, n_vessels)
        n_timepoints = max(3, n_timepoints)
        np.random.seed(1)
        ref = np.random.uniform(30, 100, (n_vessels, n_timepoints))
        tst = np.random.uniform(30, 100, (n_vessels, n_timepoints))

        r1 = bootstrap_f2(ref, tst, n_replicates=200, seed=123)
        r2 = bootstrap_f2(ref, tst, n_replicates=200, seed=123)
        assert np.isclose(r1.ci_lower, r2.ci_lower)
        assert np.isclose(r1.ci_upper, r2.ci_upper)
        assert np.isclose(r1.f2_observed, r2.f2_observed)

    @given(
        st.integers(min_value=2, max_value=5),
        st.integers(min_value=3, max_value=5),
    )
    def test_result_metadata(self, n_vessels, n_timepoints):
        n_vessels = max(2, n_vessels)
        n_timepoints = max(3, n_timepoints)
        np.random.seed(42)
        ref = np.random.uniform(30, 100, (n_vessels, n_timepoints))
        tst = np.random.uniform(30, 100, (n_vessels, n_timepoints))

        result = bootstrap_f2(ref, tst, n_replicates=200, seed=42)
        assert result.n_replicates == 200
        assert result.n_timepoints == n_timepoints
        assert result.n_reference_vessels == n_vessels
        assert result.n_test_vessels == n_vessels
        assert 0.0 <= result.f2_observed <= 100.0

    def test_identical_profiles_yield_f2_100(self):
        ref = np.array([[50.0, 60.0, 70.0, 80.0, 90.0], [50.0, 60.0, 70.0, 80.0, 90.0]])
        tst = np.array([[50.0, 60.0, 70.0, 80.0, 90.0], [50.0, 60.0, 70.0, 80.0, 90.0]])
        result = bootstrap_f2(ref, tst, n_replicates=200, seed=1)
        assert np.isclose(result.f2_observed, 100.0, atol=1e-10)
        assert result.ci_lower <= 100.0 <= result.ci_upper
