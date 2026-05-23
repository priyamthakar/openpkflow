"""Tests for sim/models.py — OneCompartmentModel and TwoCompartmentModel validation."""

from __future__ import annotations

import math

import pytest

from openpkflow.sim.models import OneCompartmentModel, TwoCompartmentModel

# ---------------------------------------------------------------------------
# OneCompartmentModel
# ---------------------------------------------------------------------------


class TestOneCompartmentModelIVBolus:
    """1-cmt IV bolus model tests."""

    def test_valid_instantiation(self) -> None:
        m = OneCompartmentModel(route="iv_bolus", CL=5.0, Vz=20.0)
        assert m.route == "iv_bolus"
        assert m.CL == 5.0
        assert m.Vz == 20.0
        assert m.CL_F is None
        assert m.Vz_F is None
        assert m.ka is None

    def test_half_life(self) -> None:
        """t1/2 = ln(2) / (CL/Vz) for IV routes."""
        m = OneCompartmentModel(route="iv_bolus", CL=10.0, Vz=50.0)
        expected = math.log(2.0) / (10.0 / 50.0)
        assert math.isclose(m.half_life, expected, rel_tol=1e-10)

    def test_params_dict(self) -> None:
        m = OneCompartmentModel(route="iv_bolus", CL=5.0, Vz=20.0)
        d = m.param_dict()
        assert d["route"] == "iv_bolus"
        assert d["CL"] == 5.0
        assert d["Vz"] == 20.0
        assert "half_life" in d
        assert "CL_F" not in d
        assert "Vz_F" not in d
        assert "ka" not in d

    def test_missing_cl_raises(self) -> None:
        with pytest.raises(ValueError, match="requires CL and Vz"):
            OneCompartmentModel(route="iv_bolus", CL=None, Vz=20.0)

    def test_missing_vz_raises(self) -> None:
        with pytest.raises(ValueError, match="requires CL and Vz"):
            OneCompartmentModel(route="iv_bolus", CL=5.0, Vz=None)

    def test_negative_cl_raises(self) -> None:
        with pytest.raises(ValueError, match="must be > 0"):
            OneCompartmentModel(route="iv_bolus", CL=-1.0, Vz=20.0)

    def test_zero_cl_raises(self) -> None:
        with pytest.raises(ValueError, match="must be > 0"):
            OneCompartmentModel(route="iv_bolus", CL=0.0, Vz=20.0)

    def test_negative_vz_raises(self) -> None:
        with pytest.raises(ValueError, match="must be > 0"):
            OneCompartmentModel(route="iv_bolus", CL=5.0, Vz=-5.0)

    def test_rejects_oral_params(self) -> None:
        with pytest.raises(ValueError, match="does not accept CL_F, Vz_F, or ka"):
            OneCompartmentModel(route="iv_bolus", CL=5.0, Vz=20.0, CL_F=10.0)

    def test_rejects_ka_on_iv(self) -> None:
        with pytest.raises(ValueError, match="does not accept CL_F, Vz_F, or ka"):
            OneCompartmentModel(route="iv_bolus", CL=5.0, Vz=20.0, ka=1.0)


class TestOneCompartmentModelIVInfusion:
    """1-cmt IV infusion model tests."""

    def test_valid_instantiation(self) -> None:
        m = OneCompartmentModel(route="iv_infusion", CL=3.0, Vz=15.0)
        assert m.route == "iv_infusion"
        assert m.CL == 3.0
        assert m.Vz == 15.0

    def test_half_life(self) -> None:
        m = OneCompartmentModel(route="iv_infusion", CL=6.0, Vz=30.0)
        expected = math.log(2.0) / (6.0 / 30.0)
        assert math.isclose(m.half_life, expected, rel_tol=1e-10)

    def test_params_dict(self) -> None:
        m = OneCompartmentModel(route="iv_infusion", CL=3.0, Vz=15.0)
        d = m.param_dict()
        assert d["route"] == "iv_infusion"
        assert d["CL"] == 3.0
        assert d["Vz"] == 15.0
        assert "CL_F" not in d

    def test_missing_vz_raises(self) -> None:
        with pytest.raises(ValueError, match="requires CL and Vz"):
            OneCompartmentModel(route="iv_infusion", CL=3.0, Vz=None)


class TestOneCompartmentModelOral:
    """1-cmt oral model tests."""

    def test_valid_instantiation(self) -> None:
        m = OneCompartmentModel(route="oral", CL_F=5.0, Vz_F=50.0, ka=1.5)
        assert m.route == "oral"
        assert m.CL_F == 5.0
        assert m.Vz_F == 50.0
        assert m.ka == 1.5
        assert m.CL is None
        assert m.Vz is None

    def test_half_life(self) -> None:
        """t1/2 = ln(2) / (CL_F/Vz_F) for oral route."""
        m = OneCompartmentModel(route="oral", CL_F=10.0, Vz_F=50.0, ka=1.5)
        expected = math.log(2.0) / (10.0 / 50.0)
        assert math.isclose(m.half_life, expected, rel_tol=1e-10)

    def test_params_dict(self) -> None:
        m = OneCompartmentModel(route="oral", CL_F=5.0, Vz_F=50.0, ka=1.5)
        d = m.param_dict()
        assert d["route"] == "oral"
        assert d["CL_F"] == 5.0
        assert d["Vz_F"] == 50.0
        assert d["ka"] == 1.5
        assert "CL" not in d
        assert "Vz" not in d

    def test_missing_clf_raises(self) -> None:
        with pytest.raises(ValueError, match="requires CL_F, Vz_F, and ka"):
            OneCompartmentModel(route="oral", Vz_F=50.0, ka=1.5)

    def test_missing_vzf_raises(self) -> None:
        with pytest.raises(ValueError, match="requires CL_F, Vz_F, and ka"):
            OneCompartmentModel(route="oral", CL_F=5.0, ka=1.5)

    def test_missing_ka_raises(self) -> None:
        with pytest.raises(ValueError, match="requires CL_F, Vz_F, and ka"):
            OneCompartmentModel(route="oral", CL_F=5.0, Vz_F=50.0)

    def test_negative_clf_raises(self) -> None:
        with pytest.raises(ValueError, match="must be > 0"):
            OneCompartmentModel(route="oral", CL_F=-1.0, Vz_F=50.0, ka=1.5)

    def test_zero_clf_raises(self) -> None:
        with pytest.raises(ValueError, match="must be > 0"):
            OneCompartmentModel(route="oral", CL_F=0.0, Vz_F=50.0, ka=1.5)

    def test_negative_vzf_raises(self) -> None:
        with pytest.raises(ValueError, match="must be > 0"):
            OneCompartmentModel(route="oral", CL_F=5.0, Vz_F=-10.0, ka=1.5)

    def test_negative_ka_raises(self) -> None:
        with pytest.raises(ValueError, match="must be > 0"):
            OneCompartmentModel(route="oral", CL_F=5.0, Vz_F=50.0, ka=-0.5)

    def test_zero_ka_raises(self) -> None:
        with pytest.raises(ValueError, match="must be > 0"):
            OneCompartmentModel(route="oral", CL_F=5.0, Vz_F=50.0, ka=0.0)

    def test_rejects_iv_params(self) -> None:
        with pytest.raises(ValueError, match="does not accept CL or Vz"):
            OneCompartmentModel(route="oral", CL_F=5.0, Vz_F=50.0, ka=1.5, CL=10.0)

    def test_rejects_vz_on_oral(self) -> None:
        with pytest.raises(ValueError, match="does not accept CL or Vz"):
            OneCompartmentModel(route="oral", CL_F=5.0, Vz_F=50.0, ka=1.5, Vz=20.0)


class TestOneCompartmentModelUnknownRoute:
    """1-cmt unknown route tests."""

    def test_unknown_route_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown route"):
            OneCompartmentModel(route="sc", CL=5.0, Vz=20.0)  # type: ignore[arg-type]

    def test_empty_route_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown route"):
            OneCompartmentModel(route="", CL=5.0, Vz=20.0)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# TwoCompartmentModel
# ---------------------------------------------------------------------------


class TestTwoCompartmentModelIVBolus:
    """2-cmt IV bolus model tests."""

    def test_valid_instantiation(self) -> None:
        m = TwoCompartmentModel(route="iv_bolus", CL=5.0, V1=20.0, Q=3.0, V2=15.0)
        assert m.route == "iv_bolus"
        assert m.CL == 5.0
        assert m.V1 == 20.0
        assert m.Q == 3.0
        assert m.V2 == 15.0
        assert m.CL_F is None
        assert m.V1_F is None
        assert m.ka is None

    def test_params_dict(self) -> None:
        m = TwoCompartmentModel(route="iv_bolus", CL=5.0, V1=20.0, Q=3.0, V2=15.0)
        d = m.param_dict()
        assert d["route"] == "iv_bolus"
        assert d["CL"] == 5.0
        assert d["V1"] == 20.0
        assert d["Q"] == 3.0
        assert d["V2"] == 15.0
        assert "CL_F" not in d
        assert "ka" not in d

    def test_missing_cl_raises(self) -> None:
        with pytest.raises(ValueError, match="requires CL and V1"):
            TwoCompartmentModel(route="iv_bolus", V1=20.0, Q=3.0, V2=15.0)

    def test_missing_v1_raises(self) -> None:
        with pytest.raises(ValueError, match="requires CL and V1"):
            TwoCompartmentModel(route="iv_bolus", CL=5.0, Q=3.0, V2=15.0)

    def test_negative_cl_raises(self) -> None:
        with pytest.raises(ValueError, match="CL and V1 must be > 0"):
            TwoCompartmentModel(route="iv_bolus", CL=-1.0, V1=20.0, Q=3.0, V2=15.0)

    def test_zero_v1_raises(self) -> None:
        with pytest.raises(ValueError, match="CL and V1 must be > 0"):
            TwoCompartmentModel(route="iv_bolus", CL=5.0, V1=0.0, Q=3.0, V2=15.0)

    def test_negative_q_raises(self) -> None:
        with pytest.raises(ValueError, match="Q must be > 0"):
            TwoCompartmentModel(route="iv_bolus", CL=5.0, V1=20.0, Q=-1.0, V2=15.0)

    def test_zero_q_raises(self) -> None:
        with pytest.raises(ValueError, match="Q must be > 0"):
            TwoCompartmentModel(route="iv_bolus", CL=5.0, V1=20.0, Q=0.0, V2=15.0)

    def test_negative_v2_raises(self) -> None:
        with pytest.raises(ValueError, match="V2 must be > 0"):
            TwoCompartmentModel(route="iv_bolus", CL=5.0, V1=20.0, Q=3.0, V2=-5.0)

    def test_rejects_oral_params(self) -> None:
        with pytest.raises(ValueError, match="does not accept CL_F, V1_F, or ka"):
            TwoCompartmentModel(route="iv_bolus", CL=5.0, V1=20.0, Q=3.0, V2=15.0, CL_F=10.0)

    def test_rejects_ka(self) -> None:
        with pytest.raises(ValueError, match="does not accept CL_F, V1_F, or ka"):
            TwoCompartmentModel(route="iv_bolus", CL=5.0, V1=20.0, Q=3.0, V2=15.0, ka=1.0)


class TestTwoCompartmentModelIVInfusion:
    """2-cmt IV infusion model tests."""

    def test_valid_instantiation(self) -> None:
        m = TwoCompartmentModel(route="iv_infusion", CL=5.0, V1=20.0, Q=3.0, V2=15.0)
        assert m.route == "iv_infusion"

    def test_params_dict(self) -> None:
        m = TwoCompartmentModel(route="iv_infusion", CL=5.0, V1=20.0, Q=3.0, V2=15.0)
        d = m.param_dict()
        assert d["route"] == "iv_infusion"
        assert d["CL"] == 5.0


class TestTwoCompartmentModelOral:
    """2-cmt oral model tests."""

    def test_valid_instantiation(self) -> None:
        m = TwoCompartmentModel(route="oral", CL_F=5.0, V1_F=20.0, Q=3.0, V2=15.0, ka=1.5)
        assert m.route == "oral"
        assert m.CL_F == 5.0
        assert m.V1_F == 20.0
        assert m.Q == 3.0
        assert m.V2 == 15.0
        assert m.ka == 1.5
        assert m.CL is None
        assert m.V1 is None

    def test_params_dict(self) -> None:
        m = TwoCompartmentModel(route="oral", CL_F=5.0, V1_F=20.0, Q=3.0, V2=15.0, ka=1.5)
        d = m.param_dict()
        assert d["route"] == "oral"
        assert d["CL_F"] == 5.0
        assert d["V1_F"] == 20.0
        assert d["ka"] == 1.5
        assert d["Q"] == 3.0
        assert d["V2"] == 15.0
        assert "CL" not in d
        assert "V1" not in d

    def test_missing_clf_raises(self) -> None:
        with pytest.raises(ValueError, match="requires CL_F, V1_F, and ka"):
            TwoCompartmentModel(route="oral", V1_F=20.0, Q=3.0, V2=15.0, ka=1.5)

    def test_missing_v1f_raises(self) -> None:
        with pytest.raises(ValueError, match="requires CL_F, V1_F, and ka"):
            TwoCompartmentModel(route="oral", CL_F=5.0, Q=3.0, V2=15.0, ka=1.5)

    def test_missing_ka_raises(self) -> None:
        with pytest.raises(ValueError, match="requires CL_F, V1_F, and ka"):
            TwoCompartmentModel(route="oral", CL_F=5.0, V1_F=20.0, Q=3.0, V2=15.0)

    def test_rejects_iv_params(self) -> None:
        with pytest.raises(ValueError, match="does not accept CL or V1"):
            TwoCompartmentModel(route="oral", CL_F=5.0, V1_F=20.0, Q=3.0, V2=15.0, ka=1.5, CL=10.0)

    def test_negative_clf_raises(self) -> None:
        with pytest.raises(ValueError, match="must be > 0"):
            TwoCompartmentModel(route="oral", CL_F=-1.0, V1_F=20.0, Q=3.0, V2=15.0, ka=1.5)


class TestTwoCompartmentModelUnknownRoute:
    """2-cmt unknown route tests."""

    def test_unknown_route_raises(self) -> None:
        with pytest.raises(ValueError, match="TwoCompartmentModel supports"):
            TwoCompartmentModel(route="im", CL=5.0, V1=20.0, Q=3.0, V2=15.0)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Frozen dataclass immutability
# ---------------------------------------------------------------------------


class TestModelImmutability:
    """Both models are frozen dataclasses and cannot be mutated."""

    def test_one_compartment_is_immutable(self) -> None:
        m = OneCompartmentModel(route="iv_bolus", CL=5.0, Vz=20.0)
        from dataclasses import FrozenInstanceError

        with pytest.raises(FrozenInstanceError):
            m.CL = 999.0  # type: ignore[misc]

    def test_two_compartment_is_immutable(self) -> None:
        m = TwoCompartmentModel(route="iv_bolus", CL=5.0, V1=20.0, Q=3.0, V2=15.0)
        from dataclasses import FrozenInstanceError

        with pytest.raises(FrozenInstanceError):
            m.Q = 999.0  # type: ignore[misc]
