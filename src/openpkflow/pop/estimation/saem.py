"""SAEM (Stochastic Approximation Expectation Maximization) — PyMC tier."""

from __future__ import annotations

import time
import warnings

import numpy as np
import pandas as pd

from .diagnostics import (
    compute_ebd_shrinkage,
)
from .model import PopPKModel
from .objective import (
    compute_foce_minus2ll,
    predict_individual,
)
from .result import PopPKResult
from .saem_kernel import saem_m_step, saem_s_step_single_subject_mcmc, saem_sa_step


def _require_pymc() -> None:
    try:
        import pymc  # noqa: F401
    except ImportError:
        raise ImportError(
            "SAEM estimation requires PyMC. Install: pip install 'openpkflow[bayes]'"
        ) from None


def run_saem(
    data: pd.DataFrame,
    model: PopPKModel,
    *,
    dose_col: str = "AMT",
    time_col: str = "TIME",
    dv_col: str = "DV",
    id_col: str = "ID",
    evid_col: str = "EVID",
    n_iterations: int = 500,
    n_burn_in: int = 200,
    alpha: float = 0.75,
    n_mcmc_steps: int = 5,
    seed: int | None = None,
    use_pymc: bool = False,
    subject: str = "",
) -> PopPKResult:
    """Run SAEM population PK estimation.

    Uses stochastic EM:
      S-step: sample individual random effects
      SA-step: stochastic approximation of sufficient statistics
      M-step: analytical update of population parameters

    Parameters
    ----------
    data : pd.DataFrame
        NONMEM-style dataset.
    model : PopPKModel
        Initial population PK model.
    dose_col : str
        Dose column.
    time_col : str
        Time column.
    dv_col : str
        Dependent variable column.
    id_col : str
        Subject ID column.
    evid_col : str
        Event ID column.
    n_iterations : int
        Total SAEM iterations.
    n_burn_in : int
        Burn-in iterations (excluded from posterior mean).
    alpha : float
        Step-size decay exponent (0.5 < alpha <= 1.0).
    n_mcmc_steps : int
        MCMC steps per subject per SAEM iteration.
    seed : int | None
        Random seed for reproducibility.
    use_pymc : bool
        If True, use PyMC for MCMC S-step. Requires [bayes] extra.
    subject : str
        Optional study label.

    Returns
    -------
    PopPKResult
    """
    if use_pymc:
        _require_pymc()

    t_start = time.perf_counter()

    _validate_data(data, dose_col, time_col, dv_col, id_col, evid_col)

    data_by_subject, obs_df_all = _prepare_subject_data(
        data, dose_col, time_col, dv_col, id_col, evid_col
    )

    n_subjects = len(data_by_subject)
    n_observations = len(obs_df_all)
    route = model.route
    param_names = model.param_names
    n_params = model.n_params
    rng = np.random.default_rng(seed)

    theta_pop = np.array([model.fixed_effects[k] for k in param_names])
    omega_diag = np.array([model.omega_diag[k] for k in param_names])
    sigma_prop = model.sigma_prop
    sigma_add = model.sigma_add

    s: dict[str, np.ndarray] = {}
    chain: list[tuple[np.ndarray, np.ndarray, float, float]] = []

    warn_list: list[str] = []
    n_burn_in = min(n_burn_in, n_iterations - 1)

    for k in range(n_iterations):
        gamma_k = 1.0 / max(1.0, (k + 1) ** alpha)
        omega_mat = np.diag(omega_diag)

        eta_samples = np.zeros((n_subjects, n_params), dtype=float)
        all_residuals_sq: list[float] = []
        all_f_pred: list[float] = []

        for si, (_subj, (t, y, dose)) in enumerate(sorted(data_by_subject.items())):
            if use_pymc:
                eta_sample = _saem_pymc_step(
                    t,
                    y,
                    dose,
                    theta_pop,
                    omega_mat,
                    sigma_prop,
                    sigma_add,
                    route,
                    n_mcmc_steps,
                    rng,
                )
            else:
                eta_sample = saem_s_step_single_subject_mcmc(
                    t,
                    y,
                    dose,
                    theta_pop,
                    omega_mat,
                    sigma_prop,
                    sigma_add,
                    route,
                    n_mcmc_steps,
                    rng,
                )
            eta_samples[si] = eta_sample

            theta_i = theta_pop * np.exp(eta_sample)
            try:
                c_pred = predict_individual(t, dose, theta_i, route)
            except (ValueError, FloatingPointError):
                c_pred = np.zeros_like(t)
            residuals = y - c_pred
            all_residuals_sq.extend((residuals**2).tolist())
            all_f_pred.extend(c_pred.tolist())

        res_sq_arr = np.array(all_residuals_sq, dtype=float)
        f_pred_arr = np.array(all_f_pred, dtype=float)

        s = saem_sa_step(s, eta_samples, res_sq_arr, f_pred_arr, gamma_k)

        theta_pop, omega_diag, sigma_prop, sigma_add = saem_m_step(
            s,
            n_subjects,
            n_observations,
        )

        if k >= n_burn_in:
            chain.append((theta_pop.copy(), omega_diag.copy(), sigma_prop, sigma_add))

    if len(chain) == 0:
        raise RuntimeError(
            "SAEM: no post-burn-in iterations. Increase n_iterations or reduce n_burn_in."
        )

    theta_pop_arr = np.array([c[0] for c in chain])
    omega_diag_arr = np.array([c[1] for c in chain])
    sigma_prop_arr = np.array([c[2] for c in chain])
    sigma_add_arr = np.array([c[3] for c in chain])

    theta_pop_final = theta_pop_arr.mean(axis=0)
    omega_diag_final = omega_diag_arr.mean(axis=0)
    sigma_prop_final = float(np.mean(sigma_prop_arr))
    sigma_add_final = float(np.mean(sigma_add_arr))

    theta_pop_se = theta_pop_arr.std(axis=0, ddof=1)
    omega_diag_se = omega_diag_arr.std(axis=0, ddof=1)
    sigma_prop_se = float(np.std(sigma_prop_arr, ddof=1))
    sigma_add_se = float(np.std(sigma_add_arr, ddof=1))

    omega_inv_final = np.diag(1.0 / np.maximum(omega_diag_final, 1e-9))

    from .foce_inner import compute_all_ebe

    ebe_dict, n_inner_failures, ebe_warns = compute_all_ebe(
        data_by_subject,
        theta_pop_final,
        omega_inv_final,
        sigma_prop_final,
        sigma_add_final,
        route,
    )
    warn_list.extend(ebe_warns)

    shrinkage = compute_ebd_shrinkage(
        np.array([ebe_dict[k] for k in sorted(ebe_dict.keys())]),
        {n: float(v) for n, v in zip(param_names, omega_diag_final, strict=False)},
        param_names,
    )

    ebe_df = _build_ebe_dataframe(ebe_dict, param_names)

    ipred, pop_pred, pop_pred_arr = _compute_predictions(
        data_by_subject,
        ebe_dict,
        theta_pop_final,
        route,
    )

    obs_times: dict[str, np.ndarray] = {}
    obs_concs: dict[str, np.ndarray] = {}
    for subj, (t, y, _d) in data_by_subject.items():
        obs_times[subj] = t
        obs_concs[subj] = y

    minus2ll = _compute_saem_minus2ll(
        data_by_subject,
        theta_pop_final,
        omega_diag_final,
        sigma_prop_final,
        sigma_add_final,
        route,
    )

    n_total_params = 2 * n_params + 2
    aic = minus2ll + 2 * n_total_params
    bic = minus2ll + n_total_params * np.log(max(1, n_observations))

    grad_norm = 0.0
    cond_num = float("nan")
    uncertainty_reliable = False

    elapsed = time.perf_counter() - t_start

    theta_pop_dict = {k: float(v) for k, v in zip(param_names, theta_pop_final, strict=False)}
    omega_dict = {k: float(v) for k, v in zip(param_names, omega_diag_final, strict=False)}

    return PopPKResult(
        method="SAEM",
        route=route,
        converged=len(chain) >= 100,
        uncertainty_reliable=uncertainty_reliable,
        n_subjects=n_subjects,
        n_observations=n_observations,
        minus2ll=minus2ll,
        aic=aic,
        bic=bic,
        theta_pop=theta_pop_dict,
        theta_se={k: float(v) for k, v in zip(param_names, theta_pop_se, strict=False)},
        omega_diag=omega_dict,
        omega_se={k: float(v) for k, v in zip(param_names, omega_diag_se, strict=False)},
        sigma_prop=sigma_prop_final,
        sigma_add=sigma_add_final,
        sigma_prop_se=sigma_prop_se,
        sigma_add_se=sigma_add_se,
        shrinkage=shrinkage,
        ebe=ebe_df,
        individual_predictions=ipred,
        population_predictions=pop_pred_arr,
        observed_times=obs_times,
        observed_concentrations=obs_concs,
        gradient_norm=float(grad_norm),
        condition_number=float(cond_num),
        n_inner_failures=n_inner_failures,
        iterations=n_iterations,
        elapsed_time=elapsed,
        warnings=warn_list,
        study_label=subject,
    )


def _saem_pymc_step(
    t: np.ndarray,
    y_obs: np.ndarray,
    dose: float,
    theta_pop: np.ndarray,
    omega: np.ndarray,
    sigma_prop: float,
    sigma_add: float,
    route: str,
    n_mcmc_steps: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """S-step using PyMC Metropolis sampling.

    Follows the same pattern as ``bayes/bayes_pk.py``:
    use ``@as_op`` for the blackbox PK log-likelihood and ``pm.Potential``.

    Returns
    -------
    np.ndarray
        Sampled eta vector ``(n_params,)``.
    """
    import math

    import pymc as pm
    import pytensor.tensor as pt
    from pytensor.compile.ops import as_op

    from openpkflow.sim.methods import c_1cmt_iv_bolus, c_1cmt_oral

    n_eta = len(theta_pop)
    omega_inv = np.linalg.inv(omega)
    seed_val = int(rng.integers(0, 2**31 - 1))

    def _log_post(eta_arr_float: np.ndarray) -> float:
        theta_i = theta_pop * np.exp(eta_arr_float)
        try:
            if route == "oral":
                c_pred = c_1cmt_oral(
                    t,
                    dose,
                    float(theta_i[0]),
                    float(theta_i[1]),
                    float(theta_i[2]),
                )
            else:
                c_pred = c_1cmt_iv_bolus(
                    t,
                    dose,
                    float(theta_i[0]),
                    float(theta_i[1]),
                )
        except (ValueError, FloatingPointError):
            return -1e12

        sd = np.sqrt((sigma_prop * np.abs(c_pred) + 1e-9) ** 2 + sigma_add**2)
        ll = float(-0.5 * np.sum(((y_obs - c_pred) / sd) ** 2 + np.log(sd**2) + np.log(2 * np.pi)))
        lp = float(eta_arr_float @ omega_inv @ eta_arr_float)
        lp += n_eta * math.log(2 * math.pi) + float(np.linalg.slogdet(omega)[1])
        lp *= -0.5
        return ll + lp

    if n_eta == 3:

        @as_op(itypes=[pt.dscalar, pt.dscalar, pt.dscalar], otypes=[pt.dscalar])
        def _pk_post(e0, e1, e2):  # type: ignore[no-untyped-def]
            return np.float64(_log_post(np.array([float(e0), float(e1), float(e2)])))

        with pm.Model():
            e0 = pm.Normal("e0", mu=0.0, sigma=np.sqrt(omega[0, 0]))
            e1 = pm.Normal("e1", mu=0.0, sigma=np.sqrt(omega[1, 1]))
            e2 = pm.Normal("e2", mu=0.0, sigma=np.sqrt(omega[2, 2]))
            pm.Potential("pk_logp", _pk_post(e0, e1, e2))
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                trace = pm.sample(
                    draws=n_mcmc_steps,
                    tune=0,
                    chains=1,
                    step=pm.Metropolis(),
                    progressbar=False,
                    compute_convergence_checks=False,
                    random_seed=seed_val,
                )
            if trace.posterior.dims["draw"] > 0:
                return np.array(
                    [
                        float(trace.posterior["e0"].values[0, -1]),
                        float(trace.posterior["e1"].values[0, -1]),
                        float(trace.posterior["e2"].values[0, -1]),
                    ]
                )

    elif n_eta == 2:

        @as_op(itypes=[pt.dscalar, pt.dscalar], otypes=[pt.dscalar])
        def _pk_post(e0, e1):
            return np.float64(_log_post(np.array([float(e0), float(e1)])))

        with pm.Model():
            e0 = pm.Normal("e0", mu=0.0, sigma=np.sqrt(omega[0, 0]))
            e1 = pm.Normal("e1", mu=0.0, sigma=np.sqrt(omega[1, 1]))
            pm.Potential("pk_logp", _pk_post(e0, e1))
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                trace = pm.sample(
                    draws=n_mcmc_steps,
                    tune=0,
                    chains=1,
                    step=pm.Metropolis(),
                    progressbar=False,
                    compute_convergence_checks=False,
                    random_seed=seed_val,
                )
            if trace.posterior.dims["draw"] > 0:
                return np.array(
                    [
                        float(trace.posterior["e0"].values[0, -1]),
                        float(trace.posterior["e1"].values[0, -1]),
                    ]
                )

    return rng.multivariate_normal(np.zeros(n_eta), omega)


def _validate_data(
    data: pd.DataFrame,
    dose_col: str,
    time_col: str,
    dv_col: str,
    id_col: str,
    evid_col: str,
) -> None:
    required = {dose_col, time_col, dv_col, id_col, evid_col}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")


def _prepare_subject_data(
    data: pd.DataFrame,
    dose_col: str,
    time_col: str,
    dv_col: str,
    id_col: str,
    evid_col: str,
) -> tuple[dict[str, tuple[np.ndarray, np.ndarray, float]], pd.DataFrame]:
    dose_rows = data[data[evid_col] == 1]
    obs_rows = data[data[evid_col] == 0]

    data_by_subject: dict[str, tuple[np.ndarray, np.ndarray, float]] = {}
    subj_ids = obs_rows[id_col].unique()

    for subj in subj_ids:
        obs_subj = obs_rows[obs_rows[id_col] == subj].sort_values(time_col)
        dose_subj = dose_rows[dose_rows[id_col] == subj].sort_values(time_col)
        if len(dose_subj) == 0:
            raise ValueError(f"Subject {subj}: no dose records found")
        total_dose = float(dose_subj[dose_col].sum())
        t = np.asarray(obs_subj[time_col], dtype=float)
        y = np.asarray(obs_subj[dv_col], dtype=float)
        if len(t) < 2:
            raise ValueError(f"Subject {subj}: need at least 2 observations; got {len(t)}")
        data_by_subject[str(subj)] = (t, y, total_dose)

    if len(data_by_subject) < 3:
        raise ValueError(f"Need at least 3 subjects; got {len(data_by_subject)}")
    return data_by_subject, obs_rows


def _build_ebe_dataframe(
    ebe_dict: dict[str, np.ndarray],
    param_names: list[str],
) -> pd.DataFrame:
    rows = []
    for subj in sorted(ebe_dict.keys()):
        row: dict[str, object] = {"ID": subj}
        for i, n in enumerate(param_names):
            row[f"eta_{n}"] = float(ebe_dict[subj][i])
        rows.append(row)
    return pd.DataFrame(rows)


def _compute_predictions(
    data_by_subject: dict[str, tuple[np.ndarray, np.ndarray, float]],
    ebe_dict: dict[str, np.ndarray],
    theta_pop: np.ndarray,
    route: str,
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray], np.ndarray]:
    ipred: dict[str, np.ndarray] = {}
    pop_pred: dict[str, np.ndarray] = {}
    pred_list: list[float] = []
    for subj in sorted(data_by_subject.keys()):
        t, _y, dose = data_by_subject[subj]
        eta_hat = ebe_dict.get(subj, np.zeros(len(theta_pop)))
        theta_i = theta_pop * np.exp(eta_hat)
        try:
            ipred[subj] = predict_individual(t, dose, theta_i, route)
        except (ValueError, FloatingPointError):
            ipred[subj] = np.zeros_like(t)
        try:
            pop_pred[subj] = predict_individual(t, dose, theta_pop, route)
        except (ValueError, FloatingPointError):
            pop_pred[subj] = np.zeros_like(t)
        pred_list.extend(pop_pred[subj].tolist())
    return ipred, pop_pred, np.array(pred_list, dtype=float)


def _compute_saem_minus2ll(
    data_by_subject: dict[str, tuple[np.ndarray, np.ndarray, float]],
    theta_pop: np.ndarray,
    omega_diag: np.ndarray,
    sigma_prop: float,
    sigma_add: float,
    route: str,
) -> float:
    """Compute approximate -2LL using FOCE-I linearization at SAEM final estimates."""
    n_params = len(theta_pop)
    omega = np.diag(omega_diag)
    omega_inv = np.diag(1.0 / omega_diag)

    from .foce_inner import compute_all_ebe

    ebe_dict, _nf, _w = compute_all_ebe(
        data_by_subject,
        theta_pop,
        omega_inv,
        sigma_prop,
        sigma_add,
        route,
    )

    total_minus2ll = 0.0
    for subj, (t, y, dose) in data_by_subject.items():
        eta_hat = ebe_dict.get(subj, np.zeros(n_params, dtype=float))
        subj_ll = compute_foce_minus2ll(
            t,
            y,
            dose,
            theta_pop,
            omega,
            sigma_prop,
            sigma_add,
            eta_hat,
            route,
        )
        total_minus2ll += subj_ll
    return total_minus2ll
