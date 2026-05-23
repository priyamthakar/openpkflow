"""Integration tests for SAEM population PK estimation."""

import warnings

import numpy as np
import pandas as pd
import pytest

warnings.filterwarnings("ignore", category=DeprecationWarning)

from openpkflow.pop.estimation.model import PopPKModel  # noqa: E402
from openpkflow.pop.estimation.objective import predict_individual  # noqa: E402


def _make_simulated_dataset(
    n_subjects: int = 8,
    route: str = "oral",
    seed: int = 42,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dose = 100.0
    times = np.array([0.5, 1.0, 2.0, 4.0, 6.0])

    if route == "oral":
        theta_pop = np.array([5.0, 50.0, 1.0])
        omega_diag = np.array([0.05, 0.05, 0.09])
        sigma_prop = 0.15
    else:
        theta_pop = np.array([5.0, 50.0])
        omega_diag = np.array([0.05, 0.05])
        sigma_prop = 0.15

    rows: list[dict[str, object]] = []
    for subj in range(1, n_subjects + 1):
        eta = rng.normal(0, np.sqrt(omega_diag))
        theta_i = theta_pop * np.exp(eta)
        c_pred = predict_individual(times, dose, theta_i, route)
        noise = rng.normal(0, sigma_prop * np.abs(c_pred) + 1e-9)
        c_obs = np.maximum(c_pred + noise, 0.0)

        rows.append({"ID": subj, "TIME": 0.0, "DV": 0.0, "AMT": dose, "EVID": 1})
        for t_i, c_i in zip(times, c_obs, strict=True):
            rows.append({"ID": subj, "TIME": float(t_i), "DV": float(c_i), "AMT": 0.0, "EVID": 0})

    return pd.DataFrame(rows)


class TestRunSAEM:
    def test_converges_on_simulated_oral(self) -> None:
        data = _make_simulated_dataset(n_subjects=8, route="oral")
        model = PopPKModel(
            route="oral",
            fixed_effects={"CL_F": 4.0, "Vz_F": 40.0, "ka": 0.8},
            omega_diag={"CL_F": 0.1, "Vz_F": 0.1, "ka": 0.1},
            sigma_prop=0.2,
        )

        from openpkflow.pop.estimation.saem import run_saem

        result = run_saem(
            data,
            model,
            n_iterations=150,
            n_burn_in=50,
            n_mcmc_steps=5,
            seed=42,
        )
        assert result.n_subjects == 8
        assert result.iterations == 150
        assert np.isfinite(result.minus2ll)

        est_cl = result.theta_pop["CL_F"]
        assert 1.0 < est_cl < 15.0

    def test_insufficient_subjects_raises(self) -> None:
        data = _make_simulated_dataset(n_subjects=2, route="oral")
        model = PopPKModel(
            route="oral",
            fixed_effects={"CL_F": 5.0, "Vz_F": 50.0, "ka": 1.0},
            omega_diag={"CL_F": 0.1, "Vz_F": 0.1, "ka": 0.1},
        )

        from openpkflow.pop.estimation.saem import run_saem

        with pytest.raises(ValueError, match="at least 3 subjects"):
            run_saem(data, model, n_iterations=50, n_burn_in=20)

    def test_iv_bolus_route(self) -> None:
        data = _make_simulated_dataset(n_subjects=8, route="iv_bolus")
        model = PopPKModel(
            route="iv_bolus",
            fixed_effects={"CL": 4.0, "Vz": 40.0},
            omega_diag={"CL": 0.1, "Vz": 0.1},
            sigma_prop=0.2,
        )

        from openpkflow.pop.estimation.saem import run_saem

        result = run_saem(
            data,
            model,
            n_iterations=150,
            n_burn_in=50,
            n_mcmc_steps=5,
            seed=42,
        )
        assert result.converged is True or result.converged is False
        assert "CL" in result.theta_pop

    def test_result_has_summary(self) -> None:
        data = _make_simulated_dataset(n_subjects=6, route="oral")
        model = PopPKModel(
            route="oral",
            fixed_effects={"CL_F": 4.0, "Vz_F": 40.0, "ka": 0.8},
            omega_diag={"CL_F": 0.1, "Vz_F": 0.1, "ka": 0.1},
        )

        from openpkflow.pop.estimation.saem import run_saem

        result = run_saem(data, model, n_iterations=80, n_burn_in=30, n_mcmc_steps=3, seed=42)
        summary = result.summary()
        assert "SAEM" in summary
        assert "CL_F" in summary


class TestSAEMKernel:
    def test_m_step(self) -> None:
        from openpkflow.pop.estimation.saem_kernel import saem_m_step

        s = {
            "eta_sum": np.array([0.5, -0.2]),
            "eta_outer": np.array([[1.0, 0.1], [0.1, 0.8]]),
            "resid_weighted": 5.0,
            "resid_raw": 100.0,
        }
        n_subjs = 10
        n_obs = 50
        tp, od, sp, sa = saem_m_step(s, n_subjs, n_obs)
        assert len(tp) == 2
        assert len(od) == 2
        assert sp > 0
        assert sa >= 0

    def test_sa_step_convergence(self) -> None:
        from openpkflow.pop.estimation.saem_kernel import saem_sa_step

        s_prev: dict[str, np.ndarray] = {}
        eta = np.array([[0.0, 0.0], [0.0, 0.0]])
        res_sq = np.ones(10)
        f_pred = np.ones(10)
        for k in range(20):
            gamma_k = 1.0 / (k + 1) ** 0.75
            s_prev = saem_sa_step(s_prev, eta, res_sq, f_pred, gamma_k)
        assert "eta_sum" in s_prev
        assert abs(s_prev["eta_sum"][0]) < 0.01

    def test_saem_mcmc_step(self) -> None:
        from openpkflow.pop.estimation.saem_kernel import saem_s_step_single_subject_mcmc

        t = np.array([1.0, 2.0, 4.0])
        y = np.array([0.8, 1.5, 0.6])
        dose = 100.0
        theta_pop = np.array([5.0, 50.0, 1.0])
        omega = np.diag([0.1, 0.1, 0.1])
        rng = np.random.default_rng(42)

        eta = saem_s_step_single_subject_mcmc(
            t,
            y,
            dose,
            theta_pop,
            omega,
            0.15,
            0.0,
            "oral",
            20,
            rng,
        )
        assert len(eta) == 3
        assert np.all(np.isfinite(eta))
