"""FOCE-I (First Order Conditional Estimation with Interaction) -- scipy tier.

Supports 1- and 2-compartment models and diagonal and full Omega matrices.
"""

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
)
from .omega import extract_omega_cov_dict, log_cholesky_to_omega
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
    """Run FOCE-I population PK estimation."""
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
    n_omega = model.n_omega_total
    n_cmt_val = model.n_cmt

    theta0 = model.to_theta()
    bounds = model.get_bounds()
    param_labels = model.param_labels

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
            n_params,
            n_omega,
            n_cmt_val,
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
    theta_pop_opt = np.exp(theta_opt[:n_params])
    L_diag_opt = theta_opt[n_params : n_params + n_omega][:n_params]
    L_off_opt = theta_opt[n_params + n_params : n_params + n_omega] if n_omega > n_params else None
    omega_opt = log_cholesky_to_omega(L_diag_opt, L_off_opt)
    omega_inv_opt = np.linalg.inv(omega_opt)
    omega_diag_opt = np.diag(omega_opt).copy()
    sigma_prop_opt = float(np.exp(theta_opt[-2]))
    sigma_add_opt = float(theta_opt[-1])

    ebe_dict, n_inner_failures, ebe_warns = compute_all_ebe(
        data_by_subject,
        theta_pop_opt,
        omega_inv_opt,
        sigma_prop_opt,
        sigma_add_opt,
        route,
        n_cmt=n_cmt_val,
    )
    warn_list.extend(ebe_warns)

    grad_norm = check_gradient_norm(
        theta_opt,
        lambda x: _foce_objective(
            x,
            data_by_subject,
            route,
            n_params,
            n_omega,
            n_cmt_val,
        ),
        warn_list,
    )

    check_multistart_agreement(converged_results, theta_opt, param_labels, warn_list)
    check_at_bounds(theta_opt, bounds, param_labels, warn_list)

    hess = numerical_hessian(
        lambda x: _foce_objective(
            x,
            data_by_subject,
            route,
            n_params,
            n_omega,
            n_cmt_val,
        ),
        theta_opt,
    )
    pos_def, cond_num, hess_inv = check_hessian(hess, warn_list)

    if hess_inv is not None:
        var_diag = np.diag(hess_inv)
        if np.any(var_diag < 0):
            hess_inv = None

    if hess_inv is not None:
        var_diag = np.diag(hess_inv)
        se_log = np.sqrt(np.abs(var_diag))
        theta_se = {k: float(theta_pop_opt[i] * se_log[i]) for i, k in enumerate(param_names)}
        omega_se: dict[str, float] = {}
        omega_off_se_dict: dict[str, float] = {}
        for i in range(n_params):
            idx = n_params + i
            if idx < len(se_log):
                omega_se[param_names[i]] = float(omega_diag_opt[i] * se_log[idx])
            else:
                omega_se[param_names[i]] = float("nan")
        if n_omega > n_params:
            off_names = []
            for col in range(n_params):
                for row in range(col + 1, n_params):
                    off_names.append(f"{param_names[row]}_{param_names[col]}")
            for j, oname in enumerate(off_names):
                idx = 2 * n_params + j
                if idx < len(se_log):
                    omega_off_se_dict[oname] = float(se_log[idx])
        sigma_prop_se_val = float(sigma_prop_opt * se_log[-2])
        sigma_add_se_val = float(se_log[-1])
        uncertainty_reliable = True
    else:
        theta_se = {k: float("nan") for k in param_names}
        omega_se = {k: float("nan") for k in param_names}
        omega_off_se_dict = {}
        sigma_prop_se_val = float("nan")
        sigma_add_se_val = float("nan")
        uncertainty_reliable = False

    shrinkage = _compute_shrinkage(ebe_dict, omega_diag_opt, param_names)

    ebe_df = _build_ebe_dataframe(ebe_dict, param_names)

    ipred, pop_pred, pop_pred_arr = _compute_predictions(
        data_by_subject,
        ebe_dict,
        theta_pop_opt,
        route,
        n_cmt=n_cmt_val,
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
    omega_off_diag_dict: dict[str, float] = {}
    if n_omega > n_params:
        omega_off_diag_dict = extract_omega_cov_dict(omega_opt, param_names)

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
        omega_off_diag=omega_off_diag_dict,
        omega_off_se=omega_off_se_dict,
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


def _validate_data(data, dose_col, time_col, dv_col, id_col, evid_col):
    required = {dose_col, time_col, dv_col, id_col, evid_col}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")


def _prepare_subject_data(data, dose_col, time_col, dv_col, id_col, evid_col):
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


def _generate_multistart(theta0, model, param_names, n_starts):
    starts = [theta0.copy()]
    if n_starts > 1:
        n_pk = len(param_names)
        x_plus = theta0.copy()
        x_minus = theta0.copy()
        for i in range(n_pk):
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
    data_by_subject,
    x0,
    bounds,
    route,
    n_params,
    n_omega,
    n_cmt,
    maxiter,
    ftol,
):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return minimize(
            lambda x: _foce_objective(x, data_by_subject, route, n_params, n_omega, n_cmt),
            x0,
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": maxiter, "ftol": ftol, "gtol": 1e-8},
        )


def _foce_objective(theta_vec, data_by_subject, route, n_params, n_omega, n_cmt):
    n_pk = n_params
    theta_pop = np.exp(theta_vec[:n_pk])
    omega_vec = theta_vec[n_pk : n_pk + n_omega]
    sigma_prop = float(np.exp(theta_vec[-2]))
    sigma_add = float(theta_vec[-1])

    if np.any(theta_pop <= 0) or sigma_prop <= 0:
        return 1e12

    L_diag = omega_vec[:n_pk]
    L_off = omega_vec[n_pk:] if len(omega_vec) > n_pk else None
    omega = log_cholesky_to_omega(L_diag, L_off)
    omega_inv = np.linalg.inv(omega)

    ebe_dict, _nf, _w = compute_all_ebe(
        data_by_subject,
        theta_pop,
        omega_inv,
        sigma_prop,
        sigma_add,
        route,
        n_cmt=n_cmt,
    )

    total_minus2ll = 0.0
    for subj, (t, y, dose) in data_by_subject.items():
        eta_hat = ebe_dict.get(subj, np.zeros(n_pk, dtype=float))
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
            n_cmt=n_cmt,
        )
        total_minus2ll += subj_ll

    return total_minus2ll


def _compute_shrinkage(ebe_dict, omega_diag, param_names):
    ebe_arr = np.array([ebe_dict[k] for k in sorted(ebe_dict.keys())])
    omega_dict = {n: float(v) for n, v in zip(param_names, omega_diag, strict=False)}
    return compute_ebd_shrinkage(ebe_arr, omega_dict, param_names)


def _build_ebe_dataframe(ebe_dict, param_names):
    rows = []
    for subj in sorted(ebe_dict.keys()):
        row: dict[str, object] = {"ID": subj}
        for i, n in enumerate(param_names):
            row[f"eta_{n}"] = float(ebe_dict[subj][i])
        rows.append(row)
    return pd.DataFrame(rows)


def _compute_predictions(data_by_subject, ebe_dict, theta_pop, route, n_cmt=1):
    ipred: dict[str, np.ndarray] = {}
    pop_pred: dict[str, np.ndarray] = {}
    pred_list: list[float] = []
    for subj in sorted(data_by_subject.keys()):
        t, _y, dose = data_by_subject[subj]
        eta_hat = ebe_dict[subj]
        theta_i = theta_pop * np.exp(eta_hat)
        try:
            ipred[subj] = predict_individual(t, dose, theta_i, route, n_cmt=n_cmt)
        except (ValueError, FloatingPointError):
            ipred[subj] = np.zeros_like(t)
        try:
            pop_pred[subj] = predict_individual(t, dose, theta_pop, route, n_cmt=n_cmt)
        except (ValueError, FloatingPointError):
            pop_pred[subj] = np.zeros_like(t)
        pred_list.extend(pop_pred[subj].tolist())
    return ipred, pop_pred, np.array(pred_list, dtype=float)
