"""Property-based tests for IVIVC Level A invariants."""

from __future__ import annotations

import numpy as np
from hypothesis import assume, given
from hypothesis import strategies as st

from openpkflow.ivivc.methods import ivivc_predictability, wagner_nelson


class TestWagnerNelson:
    @given(
        st.lists(st.floats(min_value=0.1, max_value=100.0), min_size=4, max_size=20),
        st.floats(min_value=0.01, max_value=1.0),
    )
    def test_fa_in_zero_to_one_range(self, conc, kel):
        conc = sorted(conc, reverse=False)
        times = [float(i) for i in range(len(conc))]
        result = wagner_nelson(times, conc, kel=kel)
        assert np.all(result >= 0.0)
        assert np.all(result <= 1.0 + 1e-10)

    @given(
        st.lists(st.floats(min_value=0.1, max_value=100.0), min_size=4, max_size=20),
        st.floats(min_value=0.01, max_value=1.0),
    )
    def test_fa_non_decreasing(self, conc, kel):
        conc = sorted(conc, reverse=False)
        times = [float(i) for i in range(len(conc))]
        result = wagner_nelson(times, conc, kel=kel)
        assert np.all(np.diff(result) >= -1e-10)


class TestIVIVCPredictability:
    @given(st.floats(min_value=0.1, max_value=1000.0))
    def test_pe_zero_when_pred_equals_obs(self, value):
        result = ivivc_predictability(value, value, value, value)
        assert result["%PE_Cmax"] == 0.0
        assert result["%PE_AUC"] == 0.0

    @given(
        st.floats(min_value=0.1, max_value=100.0),
        st.floats(min_value=0.11, max_value=110.0),
    )
    def test_sign_matches_direction_cmax(self, obs, pred):
        assume(abs(pred - obs) > 0.01)
        result = ivivc_predictability(obs, pred, obs, obs)
        if pred > obs:
            assert result["%PE_Cmax"] > 0.0
        else:
            assert result["%PE_Cmax"] < 0.0

    @given(st.floats(min_value=0.1, max_value=100.0))
    def test_single_form_no_overall_verdict(self, obs):
        result = ivivc_predictability(obs, obs, obs, obs)
        assert result["overall_pass"] is None
        assert result["passes_cmax"] is True
        assert result["passes_auc"] is True

    def test_flags_when_cmax_exceeds_15(self):
        result = ivivc_predictability(
            observed_cmax=100.0,
            predicted_cmax=120.0,
            observed_auc=100.0,
            predicted_auc=100.0,
        )
        assert result["passes_cmax"] is False
        assert result["passes_auc"] is True
        assert result["overall_pass"] is None
