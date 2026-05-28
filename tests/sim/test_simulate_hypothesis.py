"""Property-based tests for simulate() invariants."""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from openpkflow.sim.dosing import DoseRegimen
from openpkflow.sim.models import OneCompartmentModel, TwoCompartmentModel
from openpkflow.sim.simulate import simulate


class TestSimulate:
    @given(
        st.floats(min_value=0.05, max_value=50.0),
        st.floats(min_value=1.0, max_value=200.0),
        st.integers(min_value=1, max_value=5),
    )
    def test_result_length_equals_times_length(self, cl, vz, n_doses):
        model = OneCompartmentModel(route="iv_bolus", CL=cl, Vz=vz)
        regimen = DoseRegimen.from_repeated(
            amount=100.0, route="iv_bolus", tau=12.0, n_doses=n_doses
        )
        times = list(np.linspace(0, 24 * n_doses, 50))
        result = simulate(model, regimen, times)
        assert len(result.concs) == len(times)

    @given(
        st.floats(min_value=0.05, max_value=50.0),
        st.floats(min_value=1.0, max_value=200.0),
        st.integers(min_value=1, max_value=5),
    )
    def test_all_concentrations_nonnegative(self, cl, vz, n_doses):
        model = OneCompartmentModel(route="iv_bolus", CL=cl, Vz=vz)
        regimen = DoseRegimen.from_repeated(
            amount=100.0, route="iv_bolus", tau=12.0, n_doses=n_doses
        )
        times = list(np.linspace(0, 24 * n_doses, 50))
        result = simulate(model, regimen, times)
        assert np.all(np.array(result.concs) >= -1e-12)

    @given(
        st.floats(min_value=0.05, max_value=50.0),
        st.floats(min_value=1.0, max_value=200.0),
    )
    def test_route_mismatch_raises(self, cl, vz):
        model = OneCompartmentModel(route="iv_bolus", CL=cl, Vz=vz)
        regimen = DoseRegimen.from_repeated(amount=100.0, route="oral", tau=12.0, n_doses=1)
        with pytest.raises(ValueError):
            simulate(model, regimen, [0.0, 1.0, 2.0])

    @given(
        st.floats(min_value=0.05, max_value=50.0),
        st.floats(min_value=1.0, max_value=200.0),
    )
    def test_label_propagated_to_result(self, cl, vz):
        model = OneCompartmentModel(route="iv_bolus", CL=cl, Vz=vz)
        regimen = DoseRegimen.from_repeated(amount=100.0, route="iv_bolus", tau=12.0, n_doses=1)
        times = [0.0, 1.0, 2.0, 4.0, 8.0, 12.0]
        result = simulate(model, regimen, times, label="my_label")
        assert result.label == "my_label"

    def test_empty_times_raises(self):
        model = OneCompartmentModel(route="iv_bolus", CL=5.0, Vz=50.0)
        regimen = DoseRegimen.from_repeated(amount=100.0, route="iv_bolus", tau=12.0, n_doses=1)
        with pytest.raises(ValueError):
            simulate(model, regimen, [])

    def test_non_increasing_times_raises(self):
        model = OneCompartmentModel(route="iv_bolus", CL=5.0, Vz=50.0)
        regimen = DoseRegimen.from_repeated(amount=100.0, route="iv_bolus", tau=12.0, n_doses=1)
        with pytest.raises(ValueError):
            simulate(model, regimen, [2.0, 1.0, 3.0])

    @given(
        st.floats(min_value=0.05, max_value=50.0),
        st.floats(min_value=1.0, max_value=200.0),
        st.floats(min_value=0.1, max_value=5.0),
        st.integers(min_value=1, max_value=3),
    )
    def test_oral_simulate_nonnegative(self, cl_f, vz_f, ka, n_doses):
        model = OneCompartmentModel(route="oral", CL_F=cl_f, Vz_F=vz_f, ka=ka)
        regimen = DoseRegimen.from_repeated(amount=100.0, route="oral", tau=12.0, n_doses=n_doses)
        times = list(np.linspace(0, 24 * n_doses, 50))
        result = simulate(model, regimen, times)
        assert np.all(np.array(result.concs) >= -1e-12)

    @given(
        st.floats(min_value=0.05, max_value=50.0),
        st.floats(min_value=1.0, max_value=200.0),
        st.integers(min_value=1, max_value=3),
    )
    def test_1cmt_infusion_simulate_nonnegative(self, cl, vz, n_doses):
        model = OneCompartmentModel(route="iv_infusion", CL=cl, Vz=vz)
        regimen = DoseRegimen.from_repeated(
            amount=100.0, route="iv_infusion", tau=12.0, n_doses=n_doses, t_inf=2.0
        )
        times = list(np.linspace(0, 24 * n_doses, 50))
        result = simulate(model, regimen, times)
        assert np.all(np.array(result.concs) >= -1e-12)

    @given(
        st.floats(min_value=0.05, max_value=50.0),
        st.floats(min_value=1.0, max_value=200.0),
        st.floats(min_value=0.05, max_value=30.0),
        st.floats(min_value=1.0, max_value=150.0),
        st.integers(min_value=1, max_value=3),
    )
    def test_2cmt_iv_simulate_nonnegative(self, cl, v1, q, v2, n_doses):
        model = TwoCompartmentModel(route="iv_bolus", CL=cl, V1=v1, Q=q, V2=v2)
        regimen = DoseRegimen.from_repeated(
            amount=100.0, route="iv_bolus", tau=12.0, n_doses=n_doses
        )
        times = list(np.linspace(0, 24 * n_doses, 50))
        result = simulate(model, regimen, times)
        assert np.all(np.array(result.concs) >= -1e-10)

    @given(
        st.floats(min_value=0.05, max_value=50.0),
        st.floats(min_value=1.0, max_value=200.0),
        st.floats(min_value=0.05, max_value=30.0),
        st.floats(min_value=1.0, max_value=150.0),
        st.floats(min_value=0.1, max_value=5.0),
        st.integers(min_value=1, max_value=3),
    )
    def test_2cmt_oral_simulate_nonnegative(self, cl_f, v1_f, q, v2, ka, n_doses):
        model = TwoCompartmentModel(route="oral", CL_F=cl_f, V1_F=v1_f, Q=q, V2=v2, ka=ka)
        regimen = DoseRegimen.from_repeated(amount=100.0, route="oral", tau=12.0, n_doses=n_doses)
        times = list(np.linspace(0, 24 * n_doses, 50))
        result = simulate(model, regimen, times)
        assert np.all(np.array(result.concs) >= -1e-10)
