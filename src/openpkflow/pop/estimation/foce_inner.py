"""Per-subject EBE (Empirical Bayes Estimate) computation for FOCE-I inner loop."""

from __future__ import annotations

import warnings

import numpy as np
from scipy.optimize import minimize

from .objective import individual_log_likelihood, individual_prior_logp

_MIN_INNER_ITERS = 10
_MAX_INNER_ITERS = 100
_EBE_GTOL = 1e-8


def compute_ebe(
    t: np.ndarray,
    y_obs: np.ndarray,
    dose: float,
    theta_pop: np.ndarray,
    omega_inv: np.ndarray,
    sigma_prop: float,
    sigma_add: float,
    route: str,
    *,
    x0: np.ndarray | None = None,
    maxiter: int = _MAX_INNER_ITERS,
    gtol: float = _EBE_GTOL,
    n_cmt: int = 1,
) -> tuple[np.ndarray, float, bool]:
    """Compute EBE eta_hat for a single subject via L-BFGS-B.

    Minimizes the negative individual log-posterior:
        -[log p(y|eta) + log p(eta)]

    Parameters
    ----------
    t : np.ndarray
        Observation times (m,).
    y_obs : np.ndarray
        Observed concentrations (m,).
    dose : float
        Dose amount.
    theta_pop : np.ndarray
        Population typical values on natural scale (k,).
    omega_inv : np.ndarray
        Inverse of Omega matrix (precision, k, k).
    sigma_prop : float
        Proportional error CV.
    sigma_add : float
        Additive error SD.
    route : str
        ``"oral"`` or ``"iv_bolus"``.
    x0 : np.ndarray | None
        Initial eta guess. If None, uses zeros.
    maxiter : int
        Maximum inner loop iterations.
    gtol : float
        Gradient tolerance for convergence.
    n_cmt : int
        Number of compartments.

    Returns
    -------
    tuple
        ``(eta_hat, objective_value, converged)``.
    """
    k = len(theta_pop)
    if x0 is None:
        x0 = np.zeros(k, dtype=float)

    def objective(eta: np.ndarray) -> float:
        theta_i = theta_pop * np.exp(eta)
        ll = individual_log_likelihood(
            t, y_obs, dose, theta_i, sigma_prop, sigma_add, route, n_cmt=n_cmt
        )
        lp = individual_prior_logp(eta, omega_inv)
        return -(ll + lp)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = minimize(
            objective,
            x0,
            method="L-BFGS-B",
            jac=None,
            options={"maxiter": maxiter, "gtol": gtol, "ftol": 1e-12},
        )

    converged = result.success and result.nit >= _MIN_INNER_ITERS
    return result.x.copy(), float(result.fun), converged


def compute_all_ebe(
    data_by_subject: dict[str, tuple[np.ndarray, np.ndarray, float]],
    theta_pop: np.ndarray,
    omega_inv: np.ndarray,
    sigma_prop: float,
    sigma_add: float,
    route: str,
    *,
    warm_start: dict[str, np.ndarray] | None = None,
    n_cmt: int = 1,
) -> tuple[dict[str, np.ndarray], int, list[str]]:
    """Compute EBE for all subjects.

    Parameters
    ----------
    data_by_subject : dict
        Keyed by subject ID, values are ``(times, concs, dose)`` tuples.
    theta_pop : np.ndarray
        Population parameters on natural scale.
    omega_inv : np.ndarray
        Inverse of Omega matrix.
    sigma_prop : float
        Proportional error CV.
    sigma_add : float
        Additive error SD.
    route : str
        ``"oral"`` or ``"iv_bolus"``.
    warm_start : dict | None
        Previous EBE estimates for warm-starting.
    n_cmt : int
        Number of compartments.

    Returns
    -------
    tuple
        ``(ebe_dict, n_failures, warnings_list)``.
    """
    ebe_dict: dict[str, np.ndarray] = {}
    n_failures = 0
    warn_list: list[str] = []

    for subj, (t, y, dose) in data_by_subject.items():
        x0 = warm_start.get(subj) if warm_start else None
        eta_hat, _obj, converged = compute_ebe(
            t,
            y,
            dose,
            theta_pop,
            omega_inv,
            sigma_prop,
            sigma_add,
            route,
            x0=x0,
            n_cmt=n_cmt,
        )
        ebe_dict[subj] = eta_hat
        if not converged:
            n_failures += 1

    if n_failures > 0:
        warn_list.append(
            f"EBE optimization failed for {n_failures}/{len(data_by_subject)} subjects."
        )

    return ebe_dict, n_failures, warn_list
