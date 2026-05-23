"""Integration tests for FOCE-I population PK estimation — lightweight."""

import warnings

import numpy as np
import pandas as pd
import pytest

warnings.filterwarnings("ignore", category=DeprecationWarning)

from openpkflow.pop.estimation.model import PopPKModel  # noqa: E402
from openpkflow.pop.estimation.objective import predict_individual  # noqa: E402


def _make_simulated_dataset(
    n_subjects: int = 6,
    route: str = "iv_bolus",
    seed: int = 42,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dose = 100.0
    times = np.array([0.5, 1.0, 2.0, 4.0])

    if route == "oral":
        theta_pop = np.array([5.0, 50.0, 1.0])
        omega_diag = np.array([0.05, 0.05, 0.05])
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


class TestRunFoCEI:
    def test_converges_iv(self) -> None:
        data = _make_simulated_dataset(n_subjects=6, route="iv_bolus")
        model = PopPKModel(
            route="iv_bolus",
            fixed_effects={"CL": 5.0, "Vz": 50.0},
            omega_diag={"CL": 0.05, "Vz": 0.05},
            sigma_prop=0.15,
        )
        from openpkflow.pop.estimation.foce_i import run_foce_i

        result = run_foce_i(data, model, n_multistart=1, max_outer_iters=200)
        assert result.n_subjects == 6
        assert np.isfinite(result.minus2ll)
        est_cl = result.theta_pop["CL"]
        assert 1.0 < est_cl < 20.0

    def test_insufficient_subjects_raises(self) -> None:
        data = _make_simulated_dataset(n_subjects=2, route="iv_bolus")
        model = PopPKModel(
            route="iv_bolus",
            fixed_effects={"CL": 5.0, "Vz": 50.0},
            omega_diag={"CL": 0.1, "Vz": 0.1},
        )
        from openpkflow.pop.estimation.foce_i import run_foce_i

        with pytest.raises(ValueError, match="at least 3 subjects"):
            run_foce_i(data, model)

    def test_result_summary_to_df_ebe(self) -> None:
        data = _make_simulated_dataset(n_subjects=4, route="iv_bolus")
        model = PopPKModel(
            route="iv_bolus",
            fixed_effects={"CL": 5.0, "Vz": 50.0},
            omega_diag={"CL": 0.05, "Vz": 0.05},
            sigma_prop=0.15,
        )
        from openpkflow.pop.estimation.foce_i import run_foce_i

        result = run_foce_i(data, model, n_multistart=1, max_outer_iters=200)
        summary = result.summary()
        assert "FOCE-I" in summary
        assert result.aic > 0
        assert result.bic >= result.aic
        df = result.to_dataframe()
        assert "estimate" in df.columns
        assert len(result.ebe) == 4
        assert "eta_CL" in result.ebe.columns

    def test_plot_and_report(self) -> None:
        data = _make_simulated_dataset(n_subjects=4, route="iv_bolus")
        model = PopPKModel(
            route="iv_bolus",
            fixed_effects={"CL": 5.0, "Vz": 50.0},
            omega_diag={"CL": 0.05, "Vz": 0.05},
            sigma_prop=0.15,
        )
        from openpkflow.pop.estimation.foce_i import run_foce_i

        result = run_foce_i(data, model, n_multistart=1, max_outer_iters=200)
        result.plot(show=False)
        content = result.report("tmp_foce_test.html", fmt="html")
        assert "DOCTYPE" in content or "<html" in content
