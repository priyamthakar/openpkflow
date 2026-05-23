"""FOCE-I (First Order Conditional Estimation with Interaction) — scipy tier."""

from __future__ import annotations

import time
import warnings

import numpy as np
import pandas as pd
from scipy.optimize import OptimizeResult, minimize

from .diagnostics import (
    check_at_bounds,
    check_gradient_norm,
    check_hessian,
    check_multistart_agreement,
    compute_ebd_shrinkage,
    numerical_hessian,
)
from .foce_inner import compute_all_ebe
from .model import PopPKModel
from .objective import (
    compute_foce_minus2ll,
    predict_individual,
    unpack_theta,
)
from .result import PopPKResult

_MAX_OUTER_ITERS = 10_000
_OUTER_FTOL = 1e-12
_N_MULTISTART = 3


def run_foce_i(
    data: pd.DataFrame,
    model: PopPKModel,
    *,
    dose_col: str = "AMT",
    time_col: str = "TIME",
    dv_col: str = "DV",
    id_col: str = "ID",
    evid_col: str = "EVID",
    max_inner_iters: int = 100,
    inner_gtol: float = 1e-8,
    max_outer_iters: int = _MAX_OUTER_ITERS,
    outer_ftol: float = _OUTER_FTOL,
    n_multistart: int = _N_MULTISTART,
    subject: str = "",
) -> PopPKResult:
    """Run FOCE-I population PK estimation.

    Uses L-BFGS-B outer loop with per-subject EBE inner loops.

    Parameters
    ----------
    data : pd.DataFrame
        NONMEM-style dataset with ID, TIME, DV, AMT, EVID columns.
    model : PopPKModel
        Initial population PK model.
    dose_col : str
        Column name for dose amounts.
    time_col : str
        Column name for time.
    dv_col : str
        Column name for dependent variable (concentrations).
    id_col : str
        Column name for subject ID.
    evid_col : str
        Column name for event ID.
    max_inner_iters : int
        Maximum inner loop iterations per subject.
    inner_gtol : float
        Gradient tolerance for inner EBE optimization.
    max_outer_iters : int
        Maximum outer loop iterations.
    outer_ftol : float
        Function tolerance for outer optimization.
    n_multistart : int
        Number of multi-start runs.
    subject : str
        Optional study label.

    Returns
    -------
    PopPKResult
    """
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

    theta0 = model.to_theta()
    bounds = model.get_bounds()

    param_labels = _make_param_labels(param_names)

    multi_start_points = _generate_multistart(theta0, model, param_names, n_multistart)

    best_result: OptimizeResult | None = None
    best_obj = float("inf")
    converged_results: list[OptimizeResult] = []
    total_iterations = 0

    for _start_idx, x0 in enumerate(multi_start_points):
        result = _run_foce_outer(
            data_by_subject,
            x0,
            bounds,
            route,
            param_names,
            max_outer_iters,
            outer_ftol,
        )
        total_iterations += result.nit

        if result.success:
            converged_results.append(result)

        if result.fun < best_obj:
            best_obj = float(result.fun)
            best_result = result

    if best_result is None:
        raise RuntimeError("FOCE-I: no successful optimization run")

    converged = best_result.success
    warn_list: list[str] = []

    theta_opt = best_result.x
    theta_pop_opt, omega_diag_opt, sigma_prop_opt, sigma_add_opt = unpack_theta(theta_opt, n_params)
    omega_inv_opt = np.diag(1.0 / omega_diag_opt)

    ebe_dict, n_inner_failures, ebe_warns = compute_all_ebe(
        data_by_subject,
        theta_pop_opt,
        omega_inv_opt,
        sigma_prop_opt,
        sigma_add_opt,
        route,
    )
    warn_list.extend(ebe_warns)

    grad_norm = check_gradient_norm(
        theta_opt,
        lambda x: _foce_objective(x, data_by_subject, route, param_names),
        warn_list,
    )

    check_multistart_agreement(converged_results, theta_opt, param_labels, warn_list)

    check_at_bounds(theta_opt, bounds, param_labels, warn_list)

    hess = numerical_hessian(
        lambda x: _foce_objective(x, data_by_subject, route, param_names),
        theta_opt,
    )
    pos_def, cond_num, hess_inv = check_hessian(hess, warn_list)

    se_vec = (
        _compute_se(hess_inv, theta_pop_opt, omega_diag_opt, sigma_prop_opt, n_params)
        if hess_inv is not None
        else None
    )

    if se_vec is None:
        theta_se: dict[str, float] = {k: float("nan") for k in param_names}
        omega_se: dict[str, float] = {k: float("nan") for k in param_names}
        sigma_prop_se_val = float("nan")
        sigma_add_se_val = float("nan")
        uncertainty_reliable = False
    else:
        theta_se = {k: float(v) for k, v in zip(param_names, se_vec[:n_params], strict=False)}
        omega_se = {
            k: float(v) for k, v in zip(param_names, se_vec[n_params : 2 * n_params], strict=False)
        }
        sigma_prop_se_val = float(se_vec[-2])
        sigma_add_se_val = float(se_vec[-1])
        uncertainty_reliable = True

    shrinkage = _compute_shrinkage(ebe_dict, omega_diag_opt, param_names, n_params)

    ebe_df = _build_ebe_dataframe(ebe_dict, param_names)

    ipred, pop_pred, pop_pred_arr = _compute_predictions(
        data_by_subject, ebe_dict, theta_pop_opt, route
    )

    obs_times: dict[str, np.ndarray] = {}
    obs_concs: dict[str, np.ndarray] = {}
    for subj, (t, y, _d) in data_by_subject.items():
        obs_times[subj] = t
        obs_concs[subj] = y

    minus2ll = float(best_obj)
    n_total_params = len(theta0)
    aic = minus2ll + 2 * n_total_params
    bic = minus2ll + n_total_params * np.log(max(1, n_observations))

    elapsed = time.perf_counter() - t_start

    theta_pop_dict = {k: float(v) for k, v in zip(param_names, theta_pop_opt, strict=False)}
    omega_diag_dict = {k: float(v) for k, v in zip(param_names, omega_diag_opt, strict=False)}

    return PopPKResult(
        method="FOCE-I",
        route=route,
        converged=converged,
        uncertainty_reliable=uncertainty_reliable,
        n_subjects=n_subjects,
        n_observations=n_observations,
        minus2ll=minus2ll,
        aic=aic,
        bic=bic,
        theta_pop=theta_pop_dict,
        theta_se=theta_se,
        omega_diag=omega_diag_dict,
        omega_se=omega_se,
        sigma_prop=float(sigma_prop_opt),
        sigma_add=float(sigma_add_opt),
        sigma_prop_se=sigma_prop_se_val,
        sigma_add_se=sigma_add_se_val,
        shrinkage=shrinkage,
        ebe=ebe_df,
        individual_predictions=ipred,
        population_predictions=pop_pred_arr,
        observed_times=obs_times,
        observed_concentrations=obs_concs,
        gradient_norm=float(grad_norm),
        condition_number=float(cond_num),
        n_inner_failures=n_inner_failures,
        iterations=total_iterations,
        elapsed_time=elapsed,
        warnings=warn_list,
        study_label=subject,
    )


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
        raise ValueError(f"Need at least 3 subjects for population PK; got {len(data_by_subject)}")

    return data_by_subject, obs_rows


def _make_param_labels(param_names: list[str]) -> list[str]:
    labels: list[str] = []
    for n in param_names:
        labels.append(f"log_{n}")
    for n in param_names:
        labels.append(f"log_omega_{n}")
    labels.append("log_sigma_prop")
    labels.append("sigma_add")
    return labels


def _generate_multistart(
    theta0: np.ndarray,
    model: PopPKModel,
    param_names: list[str],
    n_starts: int,
) -> list[np.ndarray]:
    starts = [theta0.copy()]
    if n_starts > 1:
        sd_shift = 0.5
        n_params = len(param_names)
        x_plus = theta0.copy()
        x_minus = theta0.copy()
        for i in range(n_params):
            x_plus[i] += sd_shift
            x_minus[i] -= sd_shift
        for i in range(n_params, 2 * n_params):
            x_plus[i] += 0.5
            x_minus[i] -= 0.5
        x_plus[-2] = np.log(model.sigma_prop + 0.1)
        x_minus[-2] = np.log(max(0.001, model.sigma_prop - 0.05))
        if n_starts > 1:
            starts.append(x_plus)
        if n_starts > 2:
            starts.append(x_minus)
    return starts[:n_starts]


def _run_foce_outer(
    data_by_subject: dict[str, tuple[np.ndarray, np.ndarray, float]],
    x0: np.ndarray,
    bounds: list[tuple[float, float]],
    route: str,
    param_names: list[str],
    maxiter: int,
    ftol: float,
) -> OptimizeResult:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return minimize(
            lambda x: _foce_objective(x, data_by_subject, route, param_names),
            x0,
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": maxiter, "ftol": ftol, "gtol": 1e-8},
        )


def _foce_objective(
    theta_vec: np.ndarray,
    data_by_subject: dict[str, tuple[np.ndarray, np.ndarray, float]],
    route: str,
    param_names: list[str],
) -> float:
    n_params = len(param_names)
    theta_pop, omega_diag_vec, sigma_prop, sigma_add = unpack_theta(theta_vec, n_params)

    if np.any(theta_pop <= 0) or np.any(omega_diag_vec <= 0) or sigma_prop <= 0:
        return 1e12

    omega = np.diag(omega_diag_vec)
    omega_inv = np.diag(1.0 / omega_diag_vec)

    ebe_dict, _n_fail, _warns = compute_all_ebe(
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


def _compute_se(
    hess_inv: np.ndarray,
    theta_pop: np.ndarray,
    omega_diag: np.ndarray,
    sigma_prop: float,
    n_params: int,
) -> np.ndarray | None:
    """Compute standard errors from inverse Hessian via delta method.

    Parameters are optimized in log-space; delta method converts to natural scale:
      SE(theta_i) = theta_i * SE(log_theta_i)
      SE(omega_i) = omega_i * SE(log_omega_i)
      SE(sigma_prop) = sigma_prop * SE(log_sigma_prop)
      SE(sigma_add) = SE(sigma_add)  (already on natural scale)

    Returns (n_params*2 + 2,) array or None if variance diagonal is negative.
    """
    var_diag = np.diag(hess_inv)
    if np.any(var_diag < 0):
        return None

    k = 2 * n_params + 2
    se = np.zeros(k, dtype=float)

    for i in range(n_params):
        se[i] = theta_pop[i] * np.sqrt(var_diag[i])
    for i in range(n_params):
        idx = n_params + i
        se[idx] = omega_diag[i] * np.sqrt(var_diag[idx])
    se[-2] = sigma_prop * np.sqrt(var_diag[-2])
    se[-1] = np.sqrt(var_diag[-1])
    return se


def _compute_shrinkage(
    ebe_dict: dict[str, np.ndarray],
    omega_diag: np.ndarray,
    param_names: list[str],
    n_params: int,
) -> dict[str, float]:
    ebe_arr = np.array([ebe_dict[k] for k in sorted(ebe_dict.keys())])
    omega_dict = {n: float(v) for n, v in zip(param_names, omega_diag, strict=False)}
    return compute_ebd_shrinkage(ebe_arr, omega_dict, param_names)


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
        eta_hat = ebe_dict[subj]
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
