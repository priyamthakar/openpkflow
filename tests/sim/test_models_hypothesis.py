"""Property-based tests for PK model parameter containers."""

from __future__ import annotations

import math

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from openpkflow.sim.models import OneCompartmentModel, TwoCompartmentModel

_valid_cl = st.floats(min_value=0.05, max_value=50.0)
_valid_v = st.floats(min_value=1.0, max_value=200.0)
_valid_ka = st.floats(min_value=0.1, max_value=5.0)
_valid_q = st.floats(min_value=0.05, max_value=30.0)
_valid_v2 = st.floats(min_value=1.0, max_value=150.0)


class TestOneCompartmentModel:
    @given(_valid_cl, _valid_v)
    def test_half_life_formula_iv(self, cl, vz):
        m = OneCompartmentModel(route="iv_bolus", CL=cl, Vz=vz)
        expected = math.log(2.0) / (cl / vz)
        assert np.isclose(m.half_life, expected, rtol=1e-12)

    @given(_valid_cl, _valid_v)
    def test_half_life_formula_iv_infusion(self, cl, vz):
        m = OneCompartmentModel(route="iv_infusion", CL=cl, Vz=vz)
        expected = math.log(2.0) / (cl / vz)
        assert np.isclose(m.half_life, expected, rtol=1e-12)

    @given(_valid_cl, _valid_v, _valid_ka)
    def test_half_life_formula_oral(self, cl_f, vz_f, ka):
        m = OneCompartmentModel(route="oral", CL_F=cl_f, Vz_F=vz_f, ka=ka)
        expected = math.log(2.0) / (cl_f / vz_f)
        assert np.isclose(m.half_life, expected, rtol=1e-12)

    @given(_valid_cl, _valid_v)
    def test_param_dict_iv_contains_only_route_relevant_params(self, cl, vz):
        m = OneCompartmentModel(route="iv_bolus", CL=cl, Vz=vz)
        d = m.param_dict()
        assert "CL" in d and "Vz" in d
        assert "CL_F" not in d and "Vz_F" not in d and "ka" not in d
        assert d["route"] == "iv_bolus"

    @given(_valid_cl, _valid_v, _valid_ka)
    def test_param_dict_oral_contains_only_route_relevant_params(self, cl_f, vz_f, ka):
        m = OneCompartmentModel(route="oral", CL_F=cl_f, Vz_F=vz_f, ka=ka)
        d = m.param_dict()
        assert "CL_F" in d and "Vz_F" in d and "ka" in d
        assert "CL" not in d and "Vz" not in d
        assert d["route"] == "oral"

    @given(_valid_cl, _valid_v, _valid_ka)
    def test_iv_route_rejects_oral_params(self, cl, vz, ka):
        with pytest.raises(ValueError):
            OneCompartmentModel(route="iv_bolus", CL=cl, Vz=vz, CL_F=1.0)

    @given(_valid_cl, _valid_v)
    def test_oral_route_requires_oral_params(self, cl_f, vz_f):
        with pytest.raises(ValueError):
            OneCompartmentModel(route="oral", CL_F=cl_f, Vz_F=vz_f)

    @given(_valid_cl, _valid_v)
    def test_oral_route_rejects_iv_params(self, cl_f, vz_f):
        with pytest.raises(ValueError):
            OneCompartmentModel(route="oral", CL_F=cl_f, Vz_F=vz_f, ka=1.0, CL=1.0)


class TestTwoCompartmentModel:
    @given(st.floats(max_value=0.0), _valid_v2)
    def test_q_must_be_positive(self, bad_q, v2):
        with pytest.raises(ValueError):
            TwoCompartmentModel(route="iv_bolus", Q=bad_q, V2=v2, CL=1.0, V1=1.0)

    @given(_valid_q, st.floats(max_value=0.0))
    def test_v2_must_be_positive(self, q, bad_v2):
        with pytest.raises(ValueError):
            TwoCompartmentModel(route="iv_bolus", Q=q, V2=bad_v2, CL=1.0, V1=1.0)

    @given(_valid_q, _valid_v2, _valid_cl, _valid_v)
    def test_iv_route_accepts_cl_and_v1(self, q, v2, cl, v1):
        m = TwoCompartmentModel(route="iv_bolus", Q=q, V2=v2, CL=cl, V1=v1)
        d = m.param_dict()
        assert "CL" in d and "V1" in d and "Q" in d and "V2" in d
        assert "CL_F" not in d and "V1_F" not in d and "ka" not in d

    @given(_valid_q, _valid_v2, _valid_cl, _valid_v, _valid_ka)
    def test_oral_route_accepts_cl_f_and_v1_f_and_ka(self, q, v2, cl_f, v1_f, ka):
        m = TwoCompartmentModel(route="oral", Q=q, V2=v2, CL_F=cl_f, V1_F=v1_f, ka=ka)
        d = m.param_dict()
        assert "CL_F" in d and "V1_F" in d and "ka" in d and "Q" in d and "V2" in d
        assert "CL" not in d and "V1" not in d

    @given(_valid_q, _valid_v2, _valid_cl, _valid_v, _valid_ka)
    def test_iv_route_rejects_oral_params(self, q, v2, cl, v1, ka):
        with pytest.raises(ValueError):
            TwoCompartmentModel(route="iv_bolus", Q=q, V2=v2, CL=cl, V1=v1, CL_F=1.0)

    @given(_valid_q, _valid_v2, _valid_cl, _valid_v, _valid_ka)
    def test_oral_route_rejects_iv_params(self, q, v2, cl_f, v1_f, ka):
        with pytest.raises(ValueError):
            TwoCompartmentModel(route="oral", Q=q, V2=v2, CL_F=cl_f, V1_F=v1_f, ka=ka, CL=1.0)

    @given(_valid_q, _valid_v2, _valid_cl, _valid_v)
    def test_iv_infusion_accepts_cl_and_v1(self, q, v2, cl, v1):
        m = TwoCompartmentModel(route="iv_infusion", Q=q, V2=v2, CL=cl, V1=v1)
        assert q == m.Q
        assert v2 == m.V2

    @given(_valid_q, _valid_v2, _valid_cl, _valid_v)
    def test_q_and_v2_always_required(self, q, v2, cl, v1):
        m = TwoCompartmentModel(route="iv_bolus", Q=q, V2=v2, CL=cl, V1=v1)
        d = m.param_dict()
        assert d["Q"] == q
        assert d["V2"] == v2
