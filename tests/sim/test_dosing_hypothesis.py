"""Property-based tests for Dose and DoseRegimen invariants."""

from __future__ import annotations

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from openpkflow.sim.dosing import Dose, DoseRegimen

_valid_amount = st.floats(min_value=0.0, max_value=1000.0)
_valid_time = st.floats(min_value=0.0, max_value=168.0)
_valid_tinf = st.floats(min_value=0.1, max_value=24.0)
_valid_tau = st.floats(min_value=0.1, max_value=168.0)
_valid_n_doses = st.integers(min_value=1, max_value=20)
_valid_route = st.sampled_from(["iv_bolus", "iv_infusion", "oral"])


class TestDoseValidation:
    @given(st.floats(max_value=-1e-10), _valid_time, _valid_route)
    def test_negative_amount_raises(self, negative_amount, time, route):
        with pytest.raises(ValueError):
            Dose(amount=negative_amount, time=time, route=route)

    @given(_valid_amount, st.floats(max_value=-1e-10), _valid_route)
    def test_negative_time_raises(self, amount, negative_time, route):
        with pytest.raises(ValueError):
            Dose(amount=amount, time=negative_time, route=route)

    @given(
        _valid_amount,
        _valid_time,
        st.sampled_from(["iv_bolus", "oral"]),
        _valid_tinf,
    )
    def test_t_inf_only_valid_for_infusion(self, amount, time, route, t_inf):
        with pytest.raises(ValueError):
            Dose(amount=amount, time=time, route=route, t_inf=t_inf)

    @given(_valid_amount, _valid_time)
    def test_iv_infusion_without_tinf_raises(self, amount, time):
        with pytest.raises(ValueError):
            Dose(amount=amount, time=time, route="iv_infusion")

    @given(_valid_amount, _valid_time, _valid_tinf)
    def test_iv_infusion_with_tinf_ok(self, amount, time, t_inf):
        d = Dose(amount=amount, time=time, route="iv_infusion", t_inf=t_inf)
        assert d.amount == amount
        assert d.t_inf == t_inf

    @given(_valid_amount, _valid_time, st.sampled_from(["iv_bolus", "oral"]))
    def test_non_infusion_dose_ok(self, amount, time, route):
        d = Dose(amount=amount, time=time, route=route)
        assert d.t_inf is None

    @given(_valid_amount, _valid_time, _valid_route)
    def test_valid_dose_equals_self(self, amount, time, route):
        if route == "iv_infusion":
            d = Dose(amount=amount, time=time, route=route, t_inf=1.0)
        else:
            d = Dose(amount=amount, time=time, route=route)
        assert d.amount == amount
        assert d.time == time
        assert d.route == route


class TestDoseRegimenInvariants:
    @given(
        _valid_amount,
        _valid_route,
        _valid_n_doses,
        _valid_tau,
    )
    def test_from_repeated_produces_n_doses(self, amount, route, n_doses, tau):
        t_inf = 1.0 if route == "iv_infusion" else None
        regimen = DoseRegimen.from_repeated(
            amount=amount, route=route, tau=tau, n_doses=n_doses, t_inf=t_inf
        )
        assert len(regimen.doses) == n_doses

    @given(
        _valid_amount,
        _valid_route,
        st.integers(min_value=2, max_value=20),
        _valid_tau,
        _valid_time,
    )
    def test_from_repeated_times_span_correct_range(self, amount, route, n_doses, tau, t_start):
        t_inf = 1.0 if route == "iv_infusion" else None
        regimen = DoseRegimen.from_repeated(
            amount=amount, route=route, tau=tau, n_doses=n_doses, t_start=t_start, t_inf=t_inf
        )
        assert regimen.doses[0].time == t_start
        assert regimen.doses[-1].time == t_start + (n_doses - 1) * tau

    @given(
        _valid_amount,
        _valid_route,
        _valid_n_doses,
        st.floats(max_value=0.0),
    )
    def test_tau_le_zero_raises(self, amount, route, n_doses, bad_tau):
        assume(bad_tau <= 0.0)
        with pytest.raises(ValueError):
            DoseRegimen.from_repeated(amount=amount, route=route, tau=bad_tau, n_doses=n_doses)

    @given(_valid_amount, _valid_route, st.floats(min_value=-10.0, max_value=0.0))
    def test_n_doses_lt_1_raises(self, amount, route, bad_n_doses):
        n = int(bad_n_doses)
        assume(n < 1)
        with pytest.raises(ValueError):
            DoseRegimen.from_repeated(amount=amount, route=route, tau=12.0, n_doses=n)

    @given(
        _valid_amount,
        _valid_route,
        _valid_n_doses,
        _valid_tau,
    )
    def test_all_doses_same_route(self, amount, route, n_doses, tau):
        t_inf = 1.0 if route == "iv_infusion" else None
        regimen = DoseRegimen.from_repeated(
            amount=amount, route=route, tau=tau, n_doses=n_doses, t_inf=t_inf
        )
        assert regimen.route == route
        for d in regimen.doses:
            assert d.route == route

    @given(
        _valid_amount,
        _valid_route,
        _valid_n_doses,
        _valid_tau,
    )
    def test_dose_amounts_match(self, amount, route, n_doses, tau):
        t_inf = 1.0 if route == "iv_infusion" else None
        regimen = DoseRegimen.from_repeated(
            amount=amount, route=route, tau=tau, n_doses=n_doses, t_inf=t_inf
        )
        assert regimen.dose_amounts == [amount] * n_doses

    def test_empty_regimen_raises(self):
        with pytest.raises(ValueError):
            DoseRegimen(doses=())

    def test_mixed_routes_raises(self):
        with pytest.raises(ValueError):
            DoseRegimen(
                doses=(
                    Dose(amount=100, time=0, route="iv_bolus"),
                    Dose(amount=100, time=12, route="oral"),
                )
            )
