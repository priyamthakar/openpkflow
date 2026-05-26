"""Property-based tests for NCA mathematical invariants.

Uses hypothesis to assert correctness properties that should hold for
ALL valid inputs, not just hand-picked test cases.
"""

from __future__ import annotations

import numpy as np
from hypothesis import given
from hypothesis import strategies as st

from openpkflow.nca.methods import auc_linear, auc_linear_up_log_down, auc_log, cmax, tmax


def _valid_conc() -> st.SearchStrategy[list[float]]:
    return st.lists(st.floats(min_value=0.0, max_value=1000.0), min_size=2, max_size=50)


def _valid_times() -> st.SearchStrategy[list[float]]:
    return st.lists(
        st.floats(min_value=0.0, max_value=168.0, allow_nan=False, allow_infinity=False),
        min_size=2,
        max_size=50,
        unique=True,
    ).map(lambda lst: sorted(lst))


class TestAUCLinearInvariants:
    @given(st.lists(st.floats(min_value=0.0, max_value=1000.0), min_size=2, max_size=30))
    def test_nonnegative(self, conc):
        """Linear AUC must be >= 0 for non-negative concentrations."""
        times = sorted([float(i) for i in range(len(conc))])
        result = auc_linear(times, conc)
        assert result >= 0.0

    @given(st.lists(st.floats(min_value=0.0, max_value=1000.0), min_size=2, max_size=30))
    def test_all_zeros(self, conc):
        """Linear AUC must be exactly 0 when all concentrations are zero."""
        times = sorted([float(i) for i in range(len(conc))])
        conc_zero = [0.0] * len(conc)
        assert auc_linear(times, conc_zero) == 0.0

    @given(
        st.lists(st.floats(min_value=0.0, max_value=1000.0), min_size=2, max_size=30),
        st.floats(min_value=0.1, max_value=10.0),
    )
    def test_scale_invariance(self, conc, factor):
        """Scaling all concentrations by a constant scales AUC by the same constant."""
        times = sorted([float(i) for i in range(len(conc))])
        original = auc_linear(times, conc)
        scaled = auc_linear(times, [c * factor for c in conc])
        if original == 0:
            assert scaled == 0.0
        else:
            assert np.isclose(scaled / original, factor, rtol=1e-12)


class TestAUCAllMethods:
    @given(
        st.lists(st.floats(min_value=0.001, max_value=1000.0), min_size=3, max_size=30),
        st.floats(min_value=0.1, max_value=10.0),
    )
    def test_scale_linearity(self, conc, factor):
        """All AUC methods should scale linearly with concentration."""
        times = sorted([float(i) for i in range(len(conc))])

        for auc_fn in [auc_linear, auc_log, auc_linear_up_log_down]:
            original = auc_fn(times, conc)
            scaled = auc_fn(times, [c * factor for c in conc])

            orig_val = original.value if hasattr(original, "value") else original
            scaled_val = scaled.value if hasattr(scaled, "value") else scaled

            if orig_val == 0:
                assert scaled_val == 0.0
            else:
                assert np.isclose(scaled_val / orig_val, factor, rtol=1e-10)


class TestCmaxTmax:
    @given(
        st.lists(st.floats(min_value=0.0, max_value=1000.0), min_size=1, max_size=50),
    )
    def test_cmax_nonnegative(self, conc):
        """Cmax must be >= 0 for non-negative concentrations."""
        result = cmax(conc)
        assert result >= 0.0

    @given(
        st.lists(st.floats(min_value=0.0, max_value=1000.0), min_size=1, max_size=50),
    )
    def test_cmax_at_least_every_concentration(self, conc):
        """Cmax must be >= every individual concentration."""
        result = cmax(conc)
        for c in conc:
            assert result >= c

    @given(
        st.lists(st.floats(min_value=0.0, max_value=1000.0), min_size=1, max_size=50),
    )
    def test_tmax_in_times(self, conc):
        """Tmax must be one of the input times."""
        times = [float(i) for i in range(len(conc))]
        result = tmax(times, conc)
        assert result in times

    @given(
        st.lists(st.floats(min_value=0.0, max_value=1000.0), min_size=1, max_size=50),
    )
    def test_cmax_equals_at_tmax(self, conc):
        """Concentration at tmax must equal cmax."""
        times = [float(i) for i in range(len(conc))]
        t_val = tmax(times, conc)
        c_val = cmax(conc)
        idx = times.index(t_val)
        assert np.isclose(conc[idx], c_val)


class TestAUCLinearUpLogDown:
    @given(
        st.lists(st.floats(min_value=0.001, max_value=100.0), min_size=4, max_size=20),
    )
    def test_monotonic_decline(self, conc):
        """For strictly declining positive conc, log rule result >= 0."""
        conc = sorted(conc, reverse=True)
        times = [float(i) for i in range(len(conc))]
        result = auc_linear_up_log_down(times, conc)
        assert result.value >= 0.0

    @given(
        st.lists(st.floats(min_value=0.001, max_value=100.0), min_size=3, max_size=20),
    )
    def test_log_rule_nonnegative(self, conc):
        """When all points are positive and declining, result is nonnegative."""
        conc = sorted(conc, reverse=True)
        times = [float(i) for i in range(len(conc))]
        result = auc_linear_up_log_down(times, conc)
        assert result.value >= 0.0
