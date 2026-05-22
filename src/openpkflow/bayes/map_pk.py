"""MAP individual PK estimation via scipy L-BFGS-B."""

from __future__ import annotations

import math
import warnings
from typing import TYPE_CHECKING, Literal

import numpy as np
from scipy.optimize import OptimizeResult, approx_fprime, minimize

from openpkflow.sim.methods import c_1cmt_iv_bolus, c_1cmt_oral

from .priors import PKPrior

if TYPE_CHECKING:
    from .results import MapPKResult

_MIN_OBS = {"oral": 3, "iv_bolus": 2}
_GRAD_NORM_THRESH = 1e-3
_COND_WARN_THRESH = 1e6
_BOUND_MARGIN = 0.01
_MULTISTART_SPREAD_THRESH = 0.20
_PRIOR_DOM_THRESH = 0.10


def map_individual_pk(
    times: list[float] | np.ndarray,
    concentrations: list[float] | np.ndarray,
    dose: float,
    route: Literal["oral", "iv_bolus"],
    prior: PKPrior | None = None,
    *,
    subject: str = "",
) -> MapPKResult:
    """Compute MAP individual PK parameter estimates from sparse concentration data.

    Minimizes the negative log-posterior via L-BFGS-B. Parameters are optimized
    in log-space. Uses 3-start multi-start to detect identifiability issues.
    Residual error is proportional with sigma fixed at ``prior.sigma_mean``.

    The MAP objective is:
        ``-(log_prior(theta) + log_likelihood(observed | theta, model))``

    Both terms are negative (log of a probability), so their sum is <= 0 and
    the negated objective is >= 0 and decreasing toward the MAP.

    Parameters
    ----------
    times : array-like
        Sampling times in hours. Minimum observations: oral >= 3, iv_bolus >= 2.
    concentrations : array-like
        Observed concentrations at each time (same units as the dose/volume ratio).
    dose : float
        Administered dose (mg or consistent units).
    route : {"oral", "iv_bolus"}
        Route of administration. Determines model and parameter set.
    prior : PKPrior or None, optional
        Log-normal priors on PK parameters. Uses defaults if None.
    subject : str, optional
        Subject identifier for labelling the result.

    Returns
    -------
    MapPKResult
        MAP estimates, SEs, derived PK parameters, and diagnostic flags.

    Raises
    ------
    ValueError
        If ``route`` is not supported, dose <= 0, or fewer than the minimum
        required observations are provided for the route.

    References
    ----------
    Rowland & Tozer, Clinical Pharmacokinetics (2011), Ch. 3 & 5.
    Sheiner LB & Beal SL (1982) Bayesian individualization of PK: simple
    implementation and comparison with non-Bayesian methods. J Pharm Sci 71:1344-8.
    """
    from .results import MapPKResult

    t = np.asarray(times, dtype=float)
    c = np.asarray(concentrations, dtype=float)

    if route not in _MIN_OBS:
        raise ValueError(f"Unsupported route '{route}'. Choose 'oral' or 'iv_bolus'.")
    if dose <= 0:
        raise ValueError("dose must be > 0.")
    if len(t) < _MIN_OBS[route]:
        raise ValueError(
            f"Route '{route}' requires >= {_MIN_OBS[route]} observations; got {len(t)}."
        )
    if len(t) != len(c):
        raise ValueError("times and concentrations must have the same length.")

    prior = prior or PKPrior()
    warn_list: list[str] = []

    # Build objective, starting points, and bounds
    obj = _make_objective(t, c, dose, route, prior)

    if route == "oral":
        x0_list = [
            np.array([prior.log_cl_mean, prior.log_v_mean, prior.log_ka_mean]),
            np.array(
                [
                    prior.log_cl_mean + prior.log_cl_sd,
                    prior.log_v_mean + prior.log_v_sd,
                    prior.log_ka_mean + prior.log_ka_sd,
                ]
            ),
            np.array(
                [
                    prior.log_cl_mean - prior.log_cl_sd,
                    prior.log_v_mean - prior.log_v_sd,
                    prior.log_ka_mean - prior.log_ka_sd,
                ]
            ),
        ]
        bounds = [
            prior.log_cl_bounds,
            prior.log_v_bounds,
            prior.log_ka_bounds,
        ]
    else:
        x0_list = [
            np.array([prior.log_cl_mean, prior.log_v_mean]),
            np.array([prior.log_cl_mean + prior.log_cl_sd, prior.log_v_mean + prior.log_v_sd]),
            np.array([prior.log_cl_mean - prior.log_cl_sd, prior.log_v_mean - prior.log_v_sd]),
        ]
        bounds = [prior.log_cl_bounds, prior.log_v_bounds]

    # Multi-start optimization
    results: list[OptimizeResult] = [_run_minimize(obj, x0, bounds) for x0 in x0_list]
    converged_results = [r for r in results if r.success]

    if not converged_results:
        best = results[0]
        warn_list.append(
            "Optimizer did not converge from any starting point. "
            "Estimates are unreliable; do not interpret as MAP."
        )
    else:
        best = min(converged_results, key=lambda r: r.fun)

    converged = best.success
    x_opt = best.x
    obj_val = float(best.fun)

    # Gradient norm check
    grad = approx_fprime(x_opt, obj, 1e-5)
    grad_norm = float(np.linalg.norm(grad))
    if grad_norm > _GRAD_NORM_THRESH:
        warn_list.append(
            f"Gradient norm at solution = {grad_norm:.3e} > {_GRAD_NORM_THRESH}. "
            "Solution may not be at MAP."
        )

    # Multi-start agreement check
    if len(converged_results) > 1:
        _check_multistart_agreement(converged_results, x_opt, warn_list)

    # Prior-dominance check
    lp = _log_prior(x_opt, prior, route)
    ll = _log_likelihood(x_opt, t, c, dose, route, prior.sigma_mean)
    log_posterior = lp + ll
    if log_posterior < 0 and ll < _PRIOR_DOM_THRESH * abs(log_posterior):
        warn_list.append(
            "Prior-dominated fit: data are insufficient to substantially update "
            "the prior. MAP estimates closely reflect the prior rather than the data."
        )

    # Hessian, SE, and uncertainty diagnostics
    H = _numerical_hessian(obj, x_opt)
    uncertainty_reliable, cond_num, H_inv = _check_hessian(H, warn_list)

    # Parameter-at-bound check
    _check_at_bounds(x_opt, bounds, warn_list)

    # Back-transform: delta method SE(param) = param * SE(log_param)
    log_cl, log_v = x_opt[0], x_opt[1]
    CL = math.exp(log_cl)
    V = math.exp(log_v)

    cl_se: float | None = None
    v_se: float | None = None
    if uncertainty_reliable and H_inv is not None:
        cl_se = CL * math.sqrt(max(H_inv[0, 0], 0.0))
        v_se = V * math.sqrt(max(H_inv[1, 1], 0.0))

    if route == "oral":
        log_ka = x_opt[2]
        ka = math.exp(log_ka)
        ka_se = (
            ka * math.sqrt(max(H_inv[2, 2], 0.0))
            if uncertainty_reliable and H_inv is not None
            else None
        )
        k = CL / V
        half_life = math.log(2.0) / k if k > 0 else float("nan")
        AUCinf = dose / CL if CL > 0 else float("nan")
        t_dense = np.linspace(0, t[-1] * 1.5, 500)
        c_dense = c_1cmt_oral(t_dense, dose, CL, V, ka)
        Cmax = float(np.max(c_dense))
        Tmax = float(t_dense[int(np.argmax(c_dense))])
        predicted = c_1cmt_oral(t, dose, CL, V, ka).tolist()
        return MapPKResult(
            subject=subject,
            route=route,
            dose=dose,
            n_observations=len(t),
            converged=converged,
            uncertainty_reliable=uncertainty_reliable,
            CL_F=CL,
            Vz_F=V,
            ka=ka,
            CL=None,
            Vz=None,
            CL_F_se=cl_se,
            Vz_F_se=v_se,
            ka_se=ka_se,
            CL_se=None,
            Vz_se=None,
            k=k,
            half_life=half_life,
            AUCinf=AUCinf,
            Cmax=Cmax,
            Tmax=Tmax,
            gradient_norm=grad_norm,
            condition_number=cond_num,
            objective_value=obj_val,
            prior=prior,
            time_points=t.tolist(),
            observed_conc=c.tolist(),
            predicted_conc=predicted,
            warnings=warn_list,
        )
    else:
        k = CL / V
        half_life = math.log(2.0) / k if k > 0 else float("nan")
        AUCinf = dose / CL if CL > 0 else float("nan")
        t_dense = np.linspace(0, t[-1] * 1.5, 500)
        c_dense = c_1cmt_iv_bolus(t_dense, dose, CL, V)
        Cmax = float(c_dense[0])
        Tmax = 0.0
        predicted = c_1cmt_iv_bolus(t, dose, CL, V).tolist()
        return MapPKResult(
            subject=subject,
            route=route,
            dose=dose,
            n_observations=len(t),
            converged=converged,
            uncertainty_reliable=uncertainty_reliable,
            CL_F=None,
            Vz_F=None,
            ka=None,
            CL=CL,
            Vz=V,
            CL_F_se=None,
            Vz_F_se=None,
            ka_se=None,
            CL_se=cl_se,
            Vz_se=v_se,
            k=k,
            half_life=half_life,
            AUCinf=AUCinf,
            Cmax=Cmax,
            Tmax=Tmax,
            gradient_norm=grad_norm,
            condition_number=cond_num,
            objective_value=obj_val,
            prior=prior,
            time_points=t.tolist(),
            observed_conc=c.tolist(),
            predicted_conc=predicted,
            warnings=warn_list,
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _make_objective(
    t: np.ndarray,
    c: np.ndarray,
    dose: float,
    route: str,
    prior: PKPrior,
) -> Callable[[np.ndarray], float]:
    sigma = prior.sigma_mean

    def objective(x: np.ndarray) -> float:
        lp = _log_prior(x, prior, route)
        ll = _log_likelihood(x, t, c, dose, route, sigma)
        return -(lp + ll)

    return objective


def _log_prior(x: np.ndarray, prior: PKPrior, route: str) -> float:
    if route == "oral":
        return prior.log_prior_oral(x[0], x[1], x[2])
    return prior.log_prior_iv(x[0], x[1])


def _log_likelihood(
    x: np.ndarray,
    t: np.ndarray,
    c_obs: np.ndarray,
    dose: float,
    route: str,
    sigma: float,
) -> float:
    log_cl, log_v = x[0], x[1]
    CL = math.exp(log_cl)
    V = math.exp(log_v)
    try:
        if route == "oral":
            ka = math.exp(x[2])
            c_pred = c_1cmt_oral(t, dose, CL, V, ka)
        else:
            c_pred = c_1cmt_iv_bolus(t, dose, CL, V)
    except (ValueError, FloatingPointError):
        return -1e12

    ll = 0.0
    for obs, pred in zip(c_obs, c_pred, strict=False):
        sd = sigma * abs(pred) + 1e-9
        ll += -0.5 * ((obs - pred) / sd) ** 2 - math.log(sd) - 0.5 * math.log(2 * math.pi)
    return ll


def _run_minimize(
    obj: Callable[[np.ndarray], float],
    x0: np.ndarray,
    bounds: list[tuple[float, float]],
) -> OptimizeResult:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return minimize(
            obj,
            x0,
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": 10_000, "ftol": 1e-12, "gtol": 1e-8},
        )


def _numerical_hessian(f: Callable[[np.ndarray], float], x: np.ndarray) -> np.ndarray:
    n = len(x)
    eps = 1e-4
    H = np.zeros((n, n))
    grad0 = approx_fprime(x, f, eps)
    for i in range(n):
        ei = np.zeros(n)
        ei[i] = eps
        grad_plus = approx_fprime(x + ei, f, eps)
        H[i] = (grad_plus - grad0) / eps
    return np.asarray(0.5 * (H + H.T))


def _check_hessian(
    H: np.ndarray,
    warn_list: list[str],
) -> tuple[bool, float, np.ndarray | None]:
    try:
        eigvals = np.linalg.eigvalsh(H)
        cond_num = float(np.max(np.abs(eigvals)) / (np.min(np.abs(eigvals)) + 1e-300))
        if np.any(eigvals <= 0):
            warn_list.append(
                "Hessian is not positive-definite (negative eigenvalue). "
                "Standard errors are not estimable; uncertainty_reliable = False."
            )
            return False, cond_num, None
        if cond_num > _COND_WARN_THRESH:
            warn_list.append(
                f"Near-singular Hessian: condition number = {cond_num:.2e}. "
                "Standard errors may be unreliable. Common with correlated CL/V."
            )
        H_inv = np.linalg.inv(H)
        return True, cond_num, H_inv
    except np.linalg.LinAlgError:
        warn_list.append("Hessian inversion failed. Standard errors not available.")
        return False, float("nan"), None


def _check_at_bounds(
    x_opt: np.ndarray,
    bounds: list[tuple[float, float]],
    warn_list: list[str],
) -> None:
    param_names = ["log_CL", "log_V", "log_ka"]
    for i, (lo, hi) in enumerate(bounds):
        name = param_names[i] if i < len(param_names) else f"param_{i}"
        span = hi - lo
        if span > 0:
            rel_lo = (x_opt[i] - lo) / span
            rel_hi = (hi - x_opt[i]) / span
            if rel_lo < _BOUND_MARGIN or rel_hi < _BOUND_MARGIN:
                warn_list.append(
                    f"Parameter {name} is near its bound ({x_opt[i]:.4f}; "
                    f"bounds [{lo}, {hi}]). Estimate may be constrained by "
                    "the prior bound rather than the data."
                )


def _check_multistart_agreement(
    converged_results: list[OptimizeResult],
    best_x: np.ndarray,
    warn_list: list[str],
) -> None:
    for r in converged_results:
        if r.x is best_x:
            continue
        rel_diffs = np.abs(np.exp(r.x) - np.exp(best_x)) / (np.exp(best_x) + 1e-300)
        if np.any(rel_diffs > _MULTISTART_SPREAD_THRESH):
            warn_list.append(
                f"Multi-start instability: parameter estimates differ by "
                f">{int(_MULTISTART_SPREAD_THRESH * 100)}% across starting points "
                "(max relative diff = "
                f"{float(np.max(rel_diffs)) * 100:.1f}%). "
                "The model may not be identifiable from these data."
            )
            return


# Type alias for callable -- avoid importing Callable at runtime
from collections.abc import Callable  # noqa: E402 (module-level at end is fine)
