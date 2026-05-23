"""Shared diagnostics for population PK estimation — Hessian checks, convergence, shrinkage."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
from scipy.optimize import OptimizeResult  # noqa: TC002

_GRAD_NORM_THRESH = 1e-3
_COND_WARN_THRESH = 1e6
_BOUND_MARGIN = 0.01
_MULTISTART_SPREAD_THRESH = 0.20


def numerical_hessian(
    f: Callable[[np.ndarray], float],
    x: np.ndarray,
    eps: float = 1e-4,
) -> np.ndarray:
    """Compute numerical Hessian via central finite differences of gradients.

    Parameters
    ----------
    f : callable
        Objective function taking (n,) array and returning a float.
    x : np.ndarray
        Point at which to evaluate the Hessian (n,).
    eps : float
        Perturbation step size.

    Returns
    -------
    np.ndarray
        ``(n, n)`` symmetrized Hessian matrix.
    """
    n = len(x)
    base_grad = _approx_gradient(f, x, eps * 0.1)
    hess = np.zeros((n, n), dtype=float)
    for i in range(n):
        x_plus = x.copy()
        x_plus[i] += eps
        grad_plus = _approx_gradient(f, x_plus, eps * 0.1)
        hess[i, :] = (grad_plus - base_grad) / eps  # type: ignore[assignment]
    return 0.5 * (hess + hess.T)


def _approx_gradient(
    f: Callable[[np.ndarray], float],
    x: np.ndarray,
    eps: float = 1e-5,
) -> np.ndarray:
    """Forward finite-difference gradient approximation."""
    n = len(x)
    f0 = f(x)
    grad = np.zeros(n, dtype=float)
    for i in range(n):
        x_plus = x.copy()
        x_plus[i] += eps
        grad[i] = (f(x_plus) - f0) / eps
    return grad


def check_hessian(
    hess: np.ndarray,
    warn_list: list[str],
) -> tuple[bool, float, np.ndarray | None]:
    """Check Hessian positive-definiteness and condition number.

    Parameters
    ----------
    hess : np.ndarray
        ``(n, n)`` Hessian matrix.
    warn_list : list[str]
        Warning messages list to append to.

    Returns
    -------
    tuple
        ``(positive_definite, condition_number, inverse_hessian_or_None)``
    """
    try:
        eigvals = np.linalg.eigvalsh(hess)
    except np.linalg.LinAlgError:
        warn_list.append("Hessian eigenvalue decomposition failed; SEs unreliable.")
        return False, float("nan"), None

    ev_min = eigvals[0]
    ev_max = eigvals[-1]
    cond_num = float(ev_max / (abs(ev_min) + 1e-300))

    if ev_min <= 0:
        warn_list.append(
            f"Hessian is not positive-definite (min eigenvalue = {ev_min:.2e}); SEs not available."
        )
        return False, cond_num, None

    if cond_num > _COND_WARN_THRESH:
        warn_list.append(
            f"Hessian condition number {cond_num:.1e} > {_COND_WARN_THRESH:.0e}; "
            "SEs may be unreliable."
        )

    try:
        hess_inv = np.linalg.inv(hess)
    except np.linalg.LinAlgError:
        warn_list.append("Hessian inversion failed; SEs not available.")
        return False, cond_num, None

    return True, cond_num, hess_inv


def check_at_bounds(
    x_opt: np.ndarray,
    bounds: list[tuple[float, float]],
    param_labels: list[str],
    warn_list: list[str],
) -> None:
    """Check whether optimized parameters are near their bounds.

    Parameters
    ----------
    x_opt : np.ndarray
        Optimized parameter vector.
    bounds : list of tuple
        ``[(lo, hi), ...]`` pairs.
    param_labels : list of str
        Parameter names.
    warn_list : list of str
        Mutated in place with warnings.
    """
    for i, (name, (lo, hi)) in enumerate(zip(param_labels, bounds, strict=False)):
        span = hi - lo if hi is not None and lo is not None else x_opt[i]
        if lo is not None:
            rel_lo = (x_opt[i] - lo) / (span + 1e-300)
            if rel_lo < _BOUND_MARGIN:
                warn_list.append(
                    f"{name} is within {rel_lo:.1%} of lower bound {lo}; "
                    "estimate may be constrained by the bound."
                )
        if hi is not None:
            rel_hi = (hi - x_opt[i]) / (span + 1e-300)
            if rel_hi < _BOUND_MARGIN:
                warn_list.append(
                    f"{name} is within {rel_hi:.1%} of upper bound {hi}; "
                    "estimate may be constrained by the bound."
                )


def check_gradient_norm(
    x_opt: np.ndarray,
    objective: Callable[[np.ndarray], float],
    warn_list: list[str],
    *,
    eps: float = 1e-5,
) -> float:
    """Compute and check gradient norm at solution.

    Parameters
    ----------
    x_opt : np.ndarray
        Optimized parameter vector.
    objective : callable
        Objective function.
    warn_list : list of str
        Mutated in place.
    eps : float
        Finite difference step.

    Returns
    -------
    float
        Euclidean norm of the gradient.
    """
    grad = _approx_gradient(objective, x_opt, eps)
    grad_norm = float(np.sqrt(np.sum(grad**2)))
    if grad_norm > _GRAD_NORM_THRESH:
        warn_list.append(
            f"Gradient norm {grad_norm:.2e} > {_GRAD_NORM_THRESH:.1e}; "
            "solution may not be at minimum."
        )
    return grad_norm


def check_multistart_agreement(
    converged_results: list[OptimizeResult],
    best_x: np.ndarray,
    param_names: list[str],
    warn_list: list[str],
    *,
    spread_threshold: float = _MULTISTART_SPREAD_THRESH,
) -> None:
    """Check agreement across multi-start optimization runs.

    Parameters
    ----------
    converged_results : list of OptimizeResult
        Results from converged multi-start runs.
    best_x : np.ndarray
        Parameter vector from the best run.
    param_names : list of str
        Parameter names for warning messages.
    warn_list : list of str
        Mutated in place.
    spread_threshold : float
        Maximum allowed relative difference.
    """
    if len(converged_results) < 2:
        return

    for res in converged_results:
        for i, name in enumerate(param_names):
            denom = abs(best_x[i]) + 1e-300
            rel_diff = abs(res.x[i] - best_x[i]) / denom
            if rel_diff > spread_threshold:
                warn_list.append(
                    f"Multi-start disagreement: {name} varies by "
                    f">{rel_diff:.0%} across starts; identifiability concern."
                )
                return


def compute_ebd_shrinkage(
    ebe: np.ndarray,
    omega_diag: dict[str, float],
    param_names: list[str],
) -> dict[str, float]:
    """Compute EBE-based shrinkage per parameter.

    shrinkage_k = 1 - var(eta_hat_k) / omega_k^2

    Parameters
    ----------
    ebe : np.ndarray
        ``(n_subjects, n_params)`` array of EBE estimates.
    omega_diag : dict[str, float]
        Estimated Omega diagonal elements.
    param_names : list of str
        Parameter names matching ebe columns.

    Returns
    -------
    dict
        Shrinkage values per parameter, clamped to [0, 1].
    """
    if ebe.shape[0] < 2:
        return {k: 1.0 for k in param_names}

    eta_vars = np.var(ebe, axis=0, ddof=1)
    shrinkage: dict[str, float] = {}
    for i, name in enumerate(param_names):
        omega_val = omega_diag.get(name, 1.0)
        raw = 1.0 - eta_vars[i] / omega_val if omega_val > 1e-9 else 1.0
        shrinkage[name] = float(np.clip(raw, 0.0, 1.0))
    return shrinkage
