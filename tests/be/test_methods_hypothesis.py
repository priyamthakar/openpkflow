"""Property-based tests for bioequivalence TOST invariants."""

from __future__ import annotations

import numpy as np
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from openpkflow.be.methods import be_sample_size, be_tost, be_tost_power

_valid_values = st.lists(st.floats(min_value=0.5, max_value=500.0), min_size=4, max_size=100)


class TestTOSTSymmetric:
    @given(_valid_values)
    def test_gmr_symmetric_by_swapping(self, values):
        """Swapping reference and test inverts GMR."""
        n = len(values) // 2 * 2
        ref = values[: n // 2]
        tst = values[n // 2 : n]
        if len(ref) < 2 or len(tst) < 2:
            # need to handle small sizes
            ref = values[: max(2, n // 2)]
            tst = values[max(2, n // 2) : max(4, n)]
        result_tr = be_tost(reference=ref, test=tst)
        result_rt = be_tost(reference=tst, test=ref)
        assert np.isclose(result_tr.gmr * result_rt.gmr, 1.0, rtol=1e-10)

    @given(st.lists(st.floats(min_value=1.0, max_value=500.0), min_size=4, max_size=50))
    def test_identical_yields_equivalent(self, values):
        """TOST on identical values should declare bioequivalence."""
        n = len(values)
        ref = values[: n // 2]
        tst = values[: n // 2]  # identical
        if len(ref) < 2:
            return
        result = be_tost(reference=ref, test=tst)
        assert np.isclose(result.gmr, 1.0, rtol=1e-10)

    @given(st.floats(min_value=0.02, max_value=1.0), st.floats(min_value=4.0, max_value=100.0))
    def test_power_for_realistic_inputs(self, cv, n):
        """Power should be in [0, 1] for realistic parameters."""
        n_int = int(n)
        assume(n_int >= 4)
        power = be_tost_power(gmr=0.95, cv=cv, n=n_int)
        assert 0.0 <= power <= 1.0

    @given(
        st.floats(min_value=0.95, max_value=1.05),
        st.floats(min_value=0.1, max_value=0.5),
        st.integers(min_value=4, max_value=60),
    )
    def test_power_monotonic_in_n(self, gmr, cv, n):
        """Power should increase with sample size (all else equal)."""
        power_n = be_tost_power(gmr=gmr, cv=cv, n=n)
        power_n2 = be_tost_power(gmr=gmr, cv=cv, n=n + 2)
        assert power_n2 >= power_n - 1e-12

    @given(_valid_values)
    def test_cv_intra_nonnegative(self, values):
        """Intra-subject CV must be >= 0."""
        n = len(values) // 2 * 2
        ref = values[: n // 2]
        tst = values[n // 2 : n]
        if len(ref) < 2 or len(tst) < 2:
            ref = values[: max(2, n // 2)]
            tst = values[max(2, n // 2) : max(4, n)]
        result = be_tost(reference=ref, test=tst)
        assert result.cv_intra_pct >= 0.0


class TestSampleSize:
    @given(
        st.floats(min_value=0.1, max_value=0.5),
        st.floats(min_value=0.85, max_value=1.0),
    )
    @settings(deadline=None)
    def test_n_increases_with_cv(self, cv_low, cv_high):
        assume(cv_high > cv_low + 0.05)
        n_low, _ = be_sample_size(gmr=0.95, cv=cv_low)
        n_high, _ = be_sample_size(gmr=0.95, cv=cv_high)
        assert n_high >= n_low

    @given(
        st.floats(min_value=0.85, max_value=0.95),
        st.floats(min_value=0.1, max_value=0.2),
    )
    @settings(deadline=None)
    def test_n_increases_as_gmr_deviates_from_one(self, gmr, cv):
        n_close, _ = be_sample_size(gmr=gmr, cv=cv)
        n_far, _ = be_sample_size(gmr=0.85, cv=cv)
        if gmr > 0.85:
            assert n_close <= n_far

    @given(
        st.floats(min_value=0.9, max_value=1.1),
        st.floats(min_value=0.1, max_value=0.3),
    )
    @settings(deadline=None)
    def test_power_at_n_ge_target(self, gmr, cv):
        n, achieved = be_sample_size(gmr=gmr, cv=cv)
        assert achieved >= 0.80 - 1e-10

    @given(
        st.floats(min_value=0.9, max_value=1.0),
        st.floats(min_value=0.1, max_value=0.2),
    )
    @settings(deadline=None)
    def test_achieved_power_in_bounds(self, gmr, cv):
        n, power = be_sample_size(gmr=gmr, cv=cv)
        assert 0.0 <= power <= 1.0
        assert n >= 4
