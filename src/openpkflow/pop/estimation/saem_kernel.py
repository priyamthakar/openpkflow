"""SAEM kernel — S-step MCMC, SA-step sufficient statistics, M-step analytical update."""

from __future__ import annotations

import numpy as np


def saem_m_step(
    s: dict[str, np.ndarray],
    n_subjects: int,
    n_obs: int,
) -> tuple[np.ndarray, np.ndarray, float, float]:
    """Analytical M-step of SAEM.

    Given sufficient statistics, compute the updated population parameters.

    Parameters
    ----------
    s : dict
        Sufficient statistics with keys:
        - ``"eta_sum"``: ``(n_params,)`` sum of eta samples
        - ``"eta_outer"``: ``(n_params, n_params)`` sum of outer products
        - ``"resid_weighted"``: sum of (residual / pred)^2
        - ``"resid_raw"``: sum of squared residuals
    n_subjects : int
        Number of subjects.
    n_obs : int
        Total number of observations.

    Returns
    -------
    tuple
        ``(theta_pop, omega_diag, sigma_prop, sigma_add)``.
    """
    theta_pop = np.exp(s["eta_sum"] / max(n_subjects, 1))

    omega_mat = s["eta_outer"] / max(n_subjects, 1)
    omega_diag = np.maximum(np.diag(omega_mat), 1e-9)

    sigma_prop = float(np.sqrt(max(0.0, s["resid_weighted"] / max(n_obs, 1))))

    raw_mean = s["resid_raw"] / max(n_obs, 1)
    sigma_add = float(np.sqrt(max(0.0, raw_mean)))

    sigma_prop = float(np.clip(float(sigma_prop), 0.001, 2.0))
    sigma_add_val = float(np.clip(float(sigma_add), 0.0, 100.0))

    return theta_pop, omega_diag, sigma_prop, sigma_add_val


def saem_sa_step(
    s_prev: dict[str, np.ndarray],
    eta_samples: np.ndarray,
    residuals_sq: np.ndarray,
    f_pred: np.ndarray,
    gamma_k: float,
) -> dict[str, np.ndarray]:
    """Stochastic approximation update of sufficient statistics.

    Parameters
    ----------
    s_prev : dict
        Previous sufficient statistics.
    eta_samples : np.ndarray
        ``(n_subjects, n_params)`` array of eta samples from S-step.
    residuals_sq : np.ndarray
        ``(n_obs,)`` squared residuals.
    f_pred : np.ndarray
        ``(n_obs,)`` predicted concentrations.
    gamma_k : float
        Step size for iteration k.

    Returns
    -------
    dict
        Updated sufficient statistics.
    """
    n_subjects = eta_samples.shape[0]
    n_params = eta_samples.shape[1] if eta_samples.ndim > 1 else 1
    eta_2d = eta_samples.reshape(n_subjects, n_params)

    S_new = {
        "eta_sum": eta_2d.sum(axis=0),
        "eta_outer": eta_2d.T @ eta_2d,
        "resid_weighted": np.sum(residuals_sq / (np.abs(f_pred) + 1e-9) ** 2),
        "resid_raw": np.sum(residuals_sq),
    }

    if not s_prev:
        return S_new

    result: dict[str, np.ndarray] = {}
    for key, new_val in S_new.items():
        prev_val = s_prev.get(key, np.zeros_like(new_val))
        result[key] = prev_val + gamma_k * (new_val - prev_val)
    return result


def saem_s_step_single_subject_mcmc(
    t: np.ndarray,
    y_obs: np.ndarray,
    dose: float,
    theta_pop: np.ndarray,
    omega: np.ndarray,
    sigma_prop: float,
    sigma_add: float,
    route: str,
    n_mcmc_steps: int = 5,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """S-step for SAEM: sample one eta draw per subject via Metropolis.

    Simple random-walk Metropolis sampler implemented directly in numpy
    (no PyMC dependency in the kernel). PyMC is used at the orchestrator
    level in saem.py; this function provides a pure-numpy fallback.

    Parameters
    ----------
    t : np.ndarray
        Observation times.
    y_obs : np.ndarray
        Observed concentrations.
    dose : float
        Dose amount.
    theta_pop : np.ndarray
        Current population parameters (natural scale).
    omega : np.ndarray
        Current Omega matrix.
    sigma_prop : float
        Proportional error.
    sigma_add : float
        Additive error.
    route : str
        ``"oral"`` or ``"iv_bolus"``.
    n_mcmc_steps : int
        Number of MCMC steps (including burn-in).
    rng : np.random.Generator | None
        Random number generator.

    Returns
    -------
    np.ndarray
        Sampled eta vector (n_params,).
    """
    from .objective import individual_log_likelihood, individual_prior_logp

    if rng is None:
        rng = np.random.default_rng()

    n_params = len(theta_pop)
    omega_inv = np.linalg.inv(omega)

    eta = np.zeros(n_params, dtype=float)

    def log_post(eta_vec: np.ndarray) -> float:
        theta_i = theta_pop * np.exp(eta_vec)
        ll = individual_log_likelihood(t, y_obs, dose, theta_i, sigma_prop, sigma_add, route)
        lp = individual_prior_logp(eta_vec, omega_inv)
        return ll + lp

    current_lp = log_post(eta)
    proposal_sd = 0.2

    for _step in range(n_mcmc_steps):
        eta_prop = eta + rng.normal(0, proposal_sd, size=n_params)
        prop_lp = log_post(eta_prop)
        if np.isfinite(prop_lp):
            log_ratio = prop_lp - current_lp
            if log_ratio > 0 or rng.random() < np.exp(log_ratio):
                eta = eta_prop
                current_lp = prop_lp

    return eta
