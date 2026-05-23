"""Shared objective functions — -2LL, linearization, gradient helpers for FOCE-I."""

from __future__ import annotations

import numpy as np
from scipy import linalg

from openpkflow.sim.methods import (
    c_1cmt_iv_bolus,
    c_1cmt_oral,
    c_2cmt_iv_bolus,
    c_2cmt_oral,
)


def predict_individual(
    t: np.ndarray,
    dose: float,
    theta_i: np.ndarray,
    route: str,
    n_cmt: int = 1,
) -> np.ndarray:
    """Predicted concentrations for a single subject given individual parameters.

    Parameters
    ----------
    t : np.ndarray
        Observation times.
    dose : float
        Dose amount.
    theta_i : np.ndarray
        Individual parameters on natural scale, matching route + n_cmt convention.
    route : str
        ``"oral"`` or ``"iv_bolus"``.
    n_cmt : int
        Number of compartments (1 or 2).

    Returns
    -------
    np.ndarray
        Predicted concentrations.
    """
    if route == "oral" and n_cmt == 1:
        return c_1cmt_oral(t, dose, theta_i[0], theta_i[1], theta_i[2])
    if route == "oral" and n_cmt == 2:
        return c_2cmt_oral(t, dose, theta_i[0], theta_i[1], theta_i[2], theta_i[3], theta_i[4])
    if route == "iv_bolus" and n_cmt == 1:
        return c_1cmt_iv_bolus(t, dose, theta_i[0], theta_i[1])
    if route == "iv_bolus" and n_cmt == 2:
        return c_2cmt_iv_bolus(t, dose, theta_i[0], theta_i[1], theta_i[2], theta_i[3])
    raise ValueError(f"Unsupported (route={route}, n_cmt={n_cmt})")


def individual_log_likelihood(
    t: np.ndarray,
    y_obs: np.ndarray,
    dose: float,
    theta_i: np.ndarray,
    sigma_prop: float,
    sigma_add: float,
    route: str,
    n_cmt: int = 1,
) -> float:
    """Gaussian log-likelihood for one subject with combined error model.

    Parameters
    ----------
    t : np.ndarray
        Observation times.
    y_obs : np.ndarray
        Observed concentrations.
    dose : float
        Dose amount.
    theta_i : np.ndarray
        Individual parameters on natural scale.
    sigma_prop : float
        Proportional error CV.
    sigma_add : float
        Additive error SD.
    route : str
        ``"oral"`` or ``"iv_bolus"``.
    n_cmt : int
        Number of compartments.

    Returns
    -------
    float
        Log-likelihood value (natural log).
    """
    try:
        c_pred = predict_individual(t, dose, theta_i, route, n_cmt)
    except (ValueError, FloatingPointError):
        return -1e12

    sd = np.sqrt((sigma_prop * np.abs(c_pred) + 1e-9) ** 2 + sigma_add**2)
    ll = -0.5 * np.sum(((y_obs - c_pred) / sd) ** 2 + np.log(sd**2) + np.log(2 * np.pi))
    if not np.isfinite(ll):
        return -1e12
    return float(ll)


def individual_prior_logp(eta: np.ndarray, omega_inv: np.ndarray) -> float:
    """Log-prior for individual random effects: N(0, Omega).

    Parameters
    ----------
    eta : np.ndarray
        Individual random effect vector.
    omega_inv : np.ndarray
        Inverse of Omega matrix (precision).

    Returns
    -------
    float
        Log-prior value.
    """
    k = len(eta)
    sign, logdet = np.linalg.slogdet(np.linalg.inv(omega_inv))
    if sign <= 0:
        return -1e12
    lp = -0.5 * (k * np.log(2 * np.pi) + logdet + eta @ omega_inv @ eta)
    return float(lp)


def compute_linearization(
    t: np.ndarray,
    dose: float,
    theta_pop: np.ndarray,
    eta_hat: np.ndarray,
    route: str,
    *,
    eps: float = 1e-5,
    n_cmt: int = 1,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute FOCE-I linearization around eta_hat.

    f(t, eta) ≈ f_hat + G @ (eta - eta_hat)

    Parameters
    ----------
    t : np.ndarray
        Observation times (m,).
    dose : float
        Dose amount.
    theta_pop : np.ndarray
        Population parameters on natural scale.
    eta_hat : np.ndarray
        EBE estimate (k,).
    route : str
        ``"oral"`` or ``"iv_bolus"``.
    eps : float
        Finite difference step for gradient.
    n_cmt : int
        Number of compartments.

    Returns
    -------
    tuple
        ``(G, f_hat, theta_i_hat)`` where ``G`` is ``(m, k)``,
        ``f_hat`` is ``(m,)``, ``theta_i_hat`` is ``(k,)``.
    """
    theta_i_hat = theta_pop * np.exp(eta_hat)
    try:
        f_hat = predict_individual(t, dose, theta_i_hat, route, n_cmt)
    except (ValueError, FloatingPointError):
        f_hat = np.full(len(t), 0.0)

    k = len(eta_hat)
    m = len(t)
    G = np.zeros((m, k), dtype=float)

    for p in range(k):
        eta_plus = eta_hat.copy()
        eta_plus[p] += eps
        theta_plus = theta_pop * np.exp(eta_plus)
        try:
            f_plus = predict_individual(t, dose, theta_plus, route, n_cmt)
        except (ValueError, FloatingPointError):
            f_plus = f_hat
        G[:, p] = (f_plus - f_hat) / eps

    return G, f_hat, theta_i_hat


def compute_foce_minus2ll(
    t: np.ndarray,
    y_obs: np.ndarray,
    dose: float,
    theta_pop: np.ndarray,
    omega: np.ndarray,
    sigma_prop: float,
    sigma_add: float,
    eta_hat: np.ndarray,
    route: str,
    n_cmt: int = 1,
) -> float:
    """Compute FOCE-I -2LL for a single subject.

    Parameters
    ----------
    t : np.ndarray
        Observation times (m,).
    y_obs : np.ndarray
        Observed concentrations (m,).
    dose : float
        Dose amount.
    theta_pop : np.ndarray
        Population parameters (natural scale, k,).
    omega : np.ndarray
        Omega matrix (k, k).
    sigma_prop : float
        Proportional error CV.
    sigma_add : float
        Additive error SD.
    eta_hat : np.ndarray
        EBE estimate (k,).
    route : str
        ``"oral"`` or ``"iv_bolus"``.
    n_cmt : int
        Number of compartments.

    Returns
    -------
    float
        Subject contribution to -2LL.
    """
    G, f_hat, _theta_i_hat = compute_linearization(
        t, dose, theta_pop, eta_hat, route, n_cmt=n_cmt
    )

    sigma_diag = (sigma_prop * np.abs(f_hat) + 1e-9) ** 2 + sigma_add**2
    sigma_mat = np.diag(sigma_diag)

    V = G @ omega @ G.T + sigma_mat
    r = y_obs - f_hat + G @ eta_hat

    try:
        cho = linalg.cho_factor(V, lower=False, overwrite_a=False)
        logdet = 2.0 * np.sum(np.log(np.diag(cho[0])))
        quad = r @ linalg.cho_solve(cho, r)
    except (np.linalg.LinAlgError, ValueError):
        return 1e12

    m = len(y_obs)
    minus2ll = m * np.log(2 * np.pi) + logdet + quad
    return float(minus2ll)


# Backward-compatible wrappers (v2.1.0 API)


def pack_theta(
    theta_pop: np.ndarray,
    omega_diag: np.ndarray,
    sigma_prop: float,
    sigma_add: float,
) -> np.ndarray:
    """Pack diagonal-only theta vector (v2.1.0 compat)."""
    return np.concatenate(
        [
            np.log(theta_pop),
            np.log(omega_diag),
            [np.log(sigma_prop)],
            [sigma_add],
        ]
    )


def unpack_theta(
    theta_vec: np.ndarray,
    n_params: int,
) -> tuple[np.ndarray, np.ndarray, float, float]:
    """Unpack diagonal-only theta vector (v2.1.0 compat)."""
    theta_pop = np.exp(theta_vec[:n_params])
    omega_diag = np.exp(theta_vec[n_params : 2 * n_params])
    sigma_prop = float(np.exp(theta_vec[-2]))
    sigma_add = float(theta_vec[-1])
    return theta_pop, omega_diag, sigma_prop, sigma_add
