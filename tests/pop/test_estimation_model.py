"""Tests for PopPKModel."""

import warnings
from dataclasses import FrozenInstanceError

import numpy as np
import pytest

warnings.filterwarnings("ignore", category=DeprecationWarning)

from openpkflow.pop.estimation.model import PopPKModel  # noqa: E402


class TestPopPKModelOral:
    def test_basic_creation(self) -> None:
        m = PopPKModel(
            route="oral",
            fixed_effects={"CL_F": 5.0, "Vz_F": 50.0, "ka": 1.0},
            omega_diag={"CL_F": 0.1, "Vz_F": 0.1, "ka": 0.1},
        )
        assert m.route == "oral"
        assert m.n_params == 3
        assert m.n_diag_omega == 3
        assert m.param_names == ["CL_F", "Vz_F", "ka"]

    def test_missing_param_raises(self) -> None:
        with pytest.raises(ValueError, match="fixed_effects keys must be"):
            PopPKModel(
                route="oral",
                fixed_effects={"CL_F": 5.0},
                omega_diag={"CL_F": 0.1, "Vz_F": 0.1, "ka": 0.1},
            )

    def test_wrong_omega_keys_raises(self) -> None:
        with pytest.raises(ValueError, match="omega_diag keys must be"):
            PopPKModel(
                route="oral",
                fixed_effects={"CL_F": 5.0, "Vz_F": 50.0, "ka": 1.0},
                omega_diag={"CL_F": 0.1},
            )

    def test_negative_value_raises(self) -> None:
        with pytest.raises(ValueError, match="must be > 0"):
            PopPKModel(
                route="oral",
                fixed_effects={"CL_F": -1.0, "Vz_F": 50.0, "ka": 1.0},
                omega_diag={"CL_F": 0.1, "Vz_F": 0.1, "ka": 0.1},
            )

    def test_negative_sigma_raises(self) -> None:
        with pytest.raises(ValueError, match="sigma_prop must be >= 0"):
            PopPKModel(
                route="oral",
                fixed_effects={"CL_F": 5.0, "Vz_F": 50.0, "ka": 1.0},
                omega_diag={"CL_F": 0.1, "Vz_F": 0.1, "ka": 0.1},
                sigma_prop=-0.1,
            )

    def test_unsupported_route_raises(self) -> None:
        with pytest.raises(ValueError, match="Unsupported route"):
            PopPKModel(
                route="iv_infusion",
                fixed_effects={"CL": 5.0, "Vz": 50.0},
                omega_diag={"CL": 0.1, "Vz": 0.1},
            )

    def test_unsupported_n_cmt_raises(self) -> None:
        with pytest.raises(ValueError, match="n_cmt must be 1 or 2"):
            PopPKModel(
                route="oral",
                n_cmt=3,
                fixed_effects={"CL_F": 5.0, "Vz_F": 50.0, "ka": 1.0},
                omega_diag={"CL_F": 0.1, "Vz_F": 0.1, "ka": 0.1},
            )

    def test_2cmt_with_1cmt_params_raises(self) -> None:
        with pytest.raises(ValueError, match="fixed_effects keys must be"):
            PopPKModel(
                route="oral",
                n_cmt=2,
                fixed_effects={"CL_F": 5.0, "Vz_F": 50.0, "ka": 1.0},
                omega_diag={"CL_F": 0.1, "Vz_F": 0.1, "ka": 0.1},
            )

    def test_unsupported_error_model_raises(self) -> None:
        with pytest.raises(ValueError, match="Unsupported error_model"):
            PopPKModel(
                route="oral",
                fixed_effects={"CL_F": 5.0, "Vz_F": 50.0, "ka": 1.0},
                omega_diag={"CL_F": 0.1, "Vz_F": 0.1, "ka": 0.1},
                error_model="poisson",
            )

    def test_to_theta_roundtrip(self) -> None:
        m = PopPKModel(
            route="oral",
            fixed_effects={"CL_F": 5.0, "Vz_F": 50.0, "ka": 1.0},
            omega_diag={"CL_F": 0.1, "Vz_F": 0.09, "ka": 0.04},
            sigma_prop=0.15,
            sigma_add=0.01,
        )
        theta = m.to_theta()
        assert len(theta) == m.n_theta
        m2 = PopPKModel.from_theta(theta, route="oral")
        np.testing.assert_allclose(
            [m2.fixed_effects[k] for k in m2.param_names],
            [m.fixed_effects[k] for k in m.param_names],
            rtol=1e-10,
        )

    def test_get_bounds_length(self) -> None:
        m = PopPKModel(
            route="oral",
            fixed_effects={"CL_F": 5.0, "Vz_F": 50.0, "ka": 1.0},
            omega_diag={"CL_F": 0.1, "Vz_F": 0.1, "ka": 0.1},
        )
        bounds = m.get_bounds()
        assert len(bounds) == m.n_theta
        assert bounds[-1] == (0.0, None)

    def test_2cmt_oral_creation(self) -> None:
        m = PopPKModel(
            route="oral",
            n_cmt=2,
            fixed_effects={"CL_F": 5.0, "V1_F": 10.0, "Q": 5.0, "V2": 30.0, "ka": 1.0},
            omega_diag={"CL_F": 0.1, "V1_F": 0.1, "Q": 0.05, "V2": 0.05, "ka": 0.1},
        )
        assert m.n_params == 5
        assert m.param_names == ["CL_F", "V1_F", "Q", "V2", "ka"]
        assert m.n_theta == 5 + 5 + 2


class TestPopPKModelIV:
    def test_basic_creation(self) -> None:
        m = PopPKModel(
            route="iv_bolus",
            fixed_effects={"CL": 5.0, "Vz": 50.0},
            omega_diag={"CL": 0.1, "Vz": 0.1},
        )
        assert m.route == "iv_bolus"
        assert m.n_params == 2
        assert m.param_names == ["CL", "Vz"]

    def test_wrong_params_raises(self) -> None:
        with pytest.raises(ValueError, match="fixed_effects keys must be"):
            PopPKModel(
                route="iv_bolus",
                fixed_effects={"CL_F": 5.0, "Vz_F": 50.0},
                omega_diag={"CL_F": 0.1, "Vz_F": 0.1},
            )

    def test_to_theta_roundtrip_iv(self) -> None:
        m = PopPKModel(
            route="iv_bolus",
            fixed_effects={"CL": 3.0, "Vz": 30.0},
            omega_diag={"CL": 0.09, "Vz": 0.04},
        )
        theta = m.to_theta()
        assert len(theta) == m.n_theta
        m2 = PopPKModel.from_theta(theta, route="iv_bolus")
        np.testing.assert_allclose(
            [m2.fixed_effects[k] for k in m2.param_names],
            [m.fixed_effects[k] for k in m.param_names],
            rtol=1e-10,
        )

    def test_frozen(self) -> None:
        m = PopPKModel(
            route="iv_bolus",
            fixed_effects={"CL": 3.0, "Vz": 30.0},
            omega_diag={"CL": 0.1, "Vz": 0.1},
        )
        with pytest.raises(FrozenInstanceError):
            m.route = "oral"  # type: ignore[misc]
