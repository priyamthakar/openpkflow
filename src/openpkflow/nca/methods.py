"""Pure-math NCA functions: trapezoidal AUC, Cmax, Tmax, lambda_z, and derived parameters.

No file I/O, no pandas, no matplotlib. All inputs are plain Python sequences or numpy arrays.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal

import numpy as np

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AUCResult:
    """Result from a trapezoidal AUC calculation.

    Parameters
    ----------
    value : float
        Computed AUC.
    warnings : list[str]
        Interval-level fallback warnings (log-to-linear substitutions).
    """

    value: float
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class LambdaZResult:
    """Result from terminal elimination rate constant estimation.

    Parameters
    ----------
    lambda_z : float
        Terminal elimination rate constant (positive, units 1/time).
    half_life : float
        Terminal half-life = ln(2) / lambda_z.
    intercept : float
        Log-scale y-intercept from OLS fit of log(conc) ~ time.
    r_squared : float
        Coefficient of determination from the log-linear OLS fit.
    adj_r_squared : float
        Adjusted R-squared from the log-linear OLS fit.
    n_points : int
        Number of points used in the regression.
    time_start : float
        First time point in the regression window.
    time_end : float
        Last time point in the regression window.
    selected_times : list[float]
        Time points used in the regression.
    selected_concs : list[float]
        Concentrations corresponding to selected_times.
    method : str
        "auto" or "manual".
    warnings : list[str]
        Quality warnings for this estimate.
    """

    lambda_z: float
    half_life: float
    intercept: float
    r_squared: float
    adj_r_squared: float
    n_points: int
    time_start: float
    time_end: float
    selected_times: list[float]
    selected_concs: list[float]
    method: str
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Shared validation helper
# ---------------------------------------------------------------------------


def _validate_time_conc(
    times: list[float],
    concs: list[float],
    min_points: int = 2,
) -> tuple[list[float], list[float]]:
    """Validate times and concentrations for NCA calculations.

    Parameters
    ----------
    times : list[float]
        Sample times.
    concs : list[float]
        Observed concentrations.
    min_points : int, optional
        Minimum required number of points, by default 2.

    Returns
    -------
    tuple[list[float], list[float]]
        Materialised (times, concs) as float lists.

    Raises
    ------
    ValueError
        If lengths differ, fewer than min_points points, times not strictly
        increasing, or any concentration is negative.
    """
    t = [float(x) for x in times]
    c = [float(x) for x in concs]

    if len(t) != len(c):
        raise ValueError(
            f"times and concs must have the same length (got {len(t)} and {len(c)})."
        )
    if len(t) < min_points:
        raise ValueError(
            f"At least {min_points} points are required (got {len(t)})."
        )
    for i in range(len(t) - 1):
        if t[i + 1] <= t[i]:
            raise ValueError(
                f"times must be strictly increasing; times[{i}]={t[i]} >= times[{i+1}]={t[i+1]}."
            )
    for i, cv in enumerate(c):
        if cv < 0.0:
            raise ValueError(
                f"concs[{i}] = {cv} is negative; concentrations must be >= 0."
            )

    return t, c


# ---------------------------------------------------------------------------
# Trapezoidal AUC functions
# ---------------------------------------------------------------------------


def auc_linear(times: list[float], concs: list[float]) -> float:
    """Compute AUC by the linear trapezoidal rule.

    Parameters
    ----------
    times : list[float]
        Sample times, strictly increasing.
    concs : list[float]
        Observed concentrations, all >= 0.

    Returns
    -------
    float
        AUC from first to last time point.

    Raises
    ------
    ValueError
        If lengths differ, < 2 points, times not strictly increasing, or
        any concentration is negative.
    """
    t, c = _validate_time_conc(times, concs, min_points=2)
    total = 0.0
    for i in range(len(t) - 1):
        total += (c[i] + c[i + 1]) / 2.0 * (t[i + 1] - t[i])
    return total


def auc_log(times: list[float], concs: list[float]) -> AUCResult:
    """Compute AUC by the log trapezoidal rule, with linear fallback per interval.

    Intervals where either concentration is <= 0 or both concentrations are equal
    fall back to the linear rule. A warning is recorded for each fallback.

    Parameters
    ----------
    times : list[float]
        Sample times, strictly increasing.
    concs : list[float]
        Observed concentrations, all >= 0.

    Returns
    -------
    AUCResult
        Computed AUC and a list of interval-level fallback warnings.

    Raises
    ------
    ValueError
        If lengths differ, < 2 points, times not strictly increasing, or
        any concentration is negative.
    """
    t, c = _validate_time_conc(times, concs, min_points=2)
    total = 0.0
    warnings: list[str] = []
    for i in range(len(t) - 1):
        c1, c2 = c[i], c[i + 1]
        dt = t[i + 1] - t[i]
        if c1 <= 0.0 or c2 <= 0.0 or c1 == c2:
            # Log rule is invalid; fall back to linear
            warnings.append(
                f"interval [{t[i]}, {t[i+1]}]: c1 or c2 non-positive or equal,"
                " fell back to linear trapezoidal"
            )
            total += (c1 + c2) / 2.0 * dt
        else:
            total += (c1 - c2) / math.log(c1 / c2) * dt
    return AUCResult(value=total, warnings=warnings)


def auc_linear_up_log_down(times: list[float], concs: list[float]) -> AUCResult:
    """Compute AUC using the linear-up / log-down trapezoidal rule.

    Rising or flat intervals (c[i+1] >= c[i]) use the linear rule.
    Declining intervals (c[i+1] < c[i]) use the log rule when both
    concentrations are positive and unequal; otherwise fall back to linear.

    Parameters
    ----------
    times : list[float]
        Sample times, strictly increasing.
    concs : list[float]
        Observed concentrations, all >= 0.

    Returns
    -------
    AUCResult
        Computed AUC and a list of interval-level fallback warnings.

    Raises
    ------
    ValueError
        If lengths differ, < 2 points, times not strictly increasing, or
        any concentration is negative.
    """
    t, c = _validate_time_conc(times, concs, min_points=2)
    total = 0.0
    warnings: list[str] = []
    for i in range(len(t) - 1):
        c1, c2 = c[i], c[i + 1]
        dt = t[i + 1] - t[i]
        if c2 >= c1:
            # Rising or flat: linear rule
            total += (c1 + c2) / 2.0 * dt
        else:
            # Declining: use log rule if valid
            if c1 <= 0.0 or c2 <= 0.0 or c1 == c2:
                warnings.append(
                    f"interval [{t[i]}, {t[i+1]}]: c1 or c2 non-positive or equal"
                    " during declining phase, fell back to linear trapezoidal"
                )
                total += (c1 + c2) / 2.0 * dt
            else:
                total += (c1 - c2) / math.log(c1 / c2) * dt
    return AUCResult(value=total, warnings=warnings)


# ---------------------------------------------------------------------------
# Cmax and Tmax
# ---------------------------------------------------------------------------


def cmax(concs: list[float]) -> float:
    """Return the maximum observed concentration.

    Parameters
    ----------
    concs : list[float]
        Observed concentrations.

    Returns
    -------
    float
        Maximum concentration.

    Raises
    ------
    ValueError
        If concs is empty or all values are NaN.
    """
    if len(concs) == 0:
        raise ValueError("concs must not be empty.")
    arr = np.asarray(concs, dtype=float)
    if np.all(np.isnan(arr)):
        raise ValueError("All concentrations are NaN; cmax is undefined.")
    return float(np.nanmax(arr))


def tmax(times: list[float], concs: list[float]) -> float:
    """Return the time of the first occurrence of the maximum concentration.

    Parameters
    ----------
    times : list[float]
        Sample times.
    concs : list[float]
        Observed concentrations.

    Returns
    -------
    float
        Time at which the maximum concentration first occurs.

    Raises
    ------
    ValueError
        If lengths differ, either is empty, or all concentrations are NaN.
    """
    if len(times) != len(concs):
        raise ValueError(
            f"times and concs must have the same length (got {len(times)} and {len(concs)})."
        )
    if len(times) == 0:
        raise ValueError("times and concs must not be empty.")
    t = np.asarray(times, dtype=float)
    c = np.asarray(concs, dtype=float)
    if np.all(np.isnan(c)):
        raise ValueError("All concentrations are NaN; tmax is undefined.")
    # nanargmax returns index of first occurrence of max (ignores NaN)
    idx = int(np.nanargmax(c))
    return float(t[idx])


# ---------------------------------------------------------------------------
# Lambda-z estimation
# ---------------------------------------------------------------------------


def _ols_fit(
    t: np.ndarray, log_c: np.ndarray
) -> tuple[float, float, float, float]:
    """Fit log(conc) = slope * time + intercept by OLS.

    Parameters
    ----------
    t : np.ndarray
        Time points.
    log_c : np.ndarray
        log(concentration) values.

    Returns
    -------
    tuple[float, float, float, float]
        (slope, intercept, r_squared, adj_r_squared)
    """
    n = len(t)
    slope, intercept = np.polyfit(t, log_c, 1)
    predicted = slope * t + intercept
    ss_res = float(np.sum((log_c - predicted) ** 2))
    ss_tot = float(np.sum((log_c - np.mean(log_c)) ** 2))

    r2 = 0.0 if ss_tot == 0.0 else 1.0 - ss_res / ss_tot

    # Adjusted R-squared: p = 2 (slope + intercept)
    adj_r2 = 1.0 - (1.0 - r2) * (n - 1) / (n - 2)

    return float(slope), float(intercept), r2, adj_r2


def lambda_z(
    times: list[float],
    concs: list[float],
    *,
    method: Literal["auto", "manual"] = "auto",
    time_range: tuple[float, float] | None = None,
    time_points: list[float] | None = None,
) -> LambdaZResult:
    """Estimate the terminal elimination rate constant lambda_z.

    Parameters
    ----------
    times : list[float]
        Sample times, strictly increasing.
    concs : list[float]
        Observed concentrations, all >= 0.
    method : {"auto", "manual"}, optional
        Selection method, by default "auto".
    time_range : tuple[float, float] or None, optional
        For manual method: include points with time_range[0] <= t <= time_range[1].
    time_points : list[float] or None, optional
        For manual method: include exactly these time points (matched with np.isclose).

    Returns
    -------
    LambdaZResult
        Terminal rate constant and regression diagnostics.

    Raises
    ------
    ValueError
        If validation fails, fewer than 3 usable points, no negative-slope
        window found, or manual selection constraints are unsatisfied.
    """
    t_all, c_all = _validate_time_conc(times, concs, min_points=2)
    t_arr = np.asarray(t_all, dtype=float)
    c_arr = np.asarray(c_all, dtype=float)

    # ----- BAR2 (Best Adjusted R-squared) auto-selection algorithm -----
    # Mirrors the PKNCA R package approach: enumerate all terminal "tail"
    # windows (contiguous subsets of size 3..N that include the last
    # quantifiable point), fit log(conc) ~ time by OLS, require negative
    # slope, then rank by adjusted R-squared descending; tie-break by more
    # points, then longer time span.  Reference: PKNCA (Bacon et al., 2023),
    # https://cran.r-project.org/package=PKNCA
    if method == "auto":
        # Step 1: identify post-Cmax positive-concentration subset
        cmax_idx = int(np.nanargmax(c_arr))
        post_mask = np.arange(len(t_arr)) > cmax_idx
        post_mask &= c_arr > 0.0

        post_t = t_arr[post_mask]
        post_c = c_arr[post_mask]
        n_post = len(post_t)

        if n_post < 3:
            raise ValueError(
                f"Fewer than 3 usable post-Cmax positive concentrations ({n_post});"
                " lambda_z cannot be calculated."
            )

        # Step 2: enumerate tail windows (size 3 .. n_post), all including last point
        best: dict | None = None
        for window_size in range(3, n_post + 1):
            start_idx = n_post - window_size
            wt = post_t[start_idx:]
            wc = post_c[start_idx:]
            log_wc = np.log(wc)

            slope, intercept, r2, adj_r2 = _ols_fit(wt, log_wc)

            if slope >= 0.0:
                # lambda_z must be positive (declining log-linear)
                continue

            if best is None or (
                adj_r2 > best["adj_r2"]
                or (adj_r2 == best["adj_r2"] and window_size > best["n"])
                or (
                    adj_r2 == best["adj_r2"]
                    and window_size == best["n"]
                    and (wt[-1] - wt[0]) > best["span"]
                )
            ):
                best = {
                    "slope": slope,
                    "intercept": intercept,
                    "r2": r2,
                    "adj_r2": adj_r2,
                    "n": window_size,
                    "span": float(wt[-1] - wt[0]),
                    "wt": wt.tolist(),
                    "wc": wc.tolist(),
                }

        if best is None:
            raise ValueError(
                "No window with a negative log-linear slope was found in the"
                " post-Cmax data; lambda_z cannot be estimated."
            )

        lz = -best["slope"]
        hl = math.log(2) / lz
        lz_warnings: list[str] = []
        if best["adj_r2"] < 0.9:
            lz_warnings.append(
                f"lambda_z auto-selected window has adjusted R2 < 0.9"
                f" ({best['adj_r2']:.4f}) -- terminal fit quality is poor"
            )

        return LambdaZResult(
            lambda_z=lz,
            half_life=hl,
            intercept=best["intercept"],
            r_squared=best["r2"],
            adj_r_squared=best["adj_r2"],
            n_points=best["n"],
            time_start=best["wt"][0],
            time_end=best["wt"][-1],
            selected_times=best["wt"],
            selected_concs=best["wc"],
            method="auto",
            warnings=lz_warnings,
        )

    elif method == "manual":
        if time_range is not None and time_points is not None:
            raise ValueError(
                "Specify either time_range or time_points for manual selection, not both."
            )
        if time_range is not None:
            t_start, t_end = float(time_range[0]), float(time_range[1])
            mask = (t_arr >= t_start) & (t_arr <= t_end)
            sel_t = t_arr[mask]
            sel_c = c_arr[mask]
        elif time_points is not None:
            tp_arr = np.asarray([float(x) for x in time_points])
            indices = []
            for tp in tp_arr:
                matches = np.where(np.isclose(t_arr, tp))[0]
                if len(matches) == 0:
                    raise ValueError(
                        f"Manual time point {tp} not found in times array"
                        " (checked with np.isclose default tolerance)."
                    )
                indices.append(int(matches[0]))
            indices_sorted = sorted(set(indices))
            sel_t = t_arr[indices_sorted]
            sel_c = c_arr[indices_sorted]
        else:
            raise ValueError(
                "method='manual' requires either time_range or time_points."
            )

        # Require positive concentrations for log-linear regression
        pos_mask = sel_c > 0.0
        sel_t = sel_t[pos_mask]
        sel_c = sel_c[pos_mask]

        if len(sel_t) < 3:
            raise ValueError(
                f"Manual selection produced fewer than 3 positive-concentration"
                f" points ({len(sel_t)}); lambda_z requires at least 3."
            )

        log_sel_c = np.log(sel_c)
        slope, intercept, r2, adj_r2 = _ols_fit(sel_t, log_sel_c)

        if slope >= 0.0:
            raise ValueError(
                "Manual selection produced a non-negative OLS slope"
                f" ({slope:.6g}); lambda_z must come from a declining log-linear fit."
            )

        lz = -slope
        hl = math.log(2) / lz
        lz_warnings: list[str] = []
        if adj_r2 < 0.9:
            lz_warnings.append(
                f"lambda_z manual window has adjusted R2 < 0.9"
                f" ({adj_r2:.4f}) -- terminal fit quality is poor"
            )

        return LambdaZResult(
            lambda_z=lz,
            half_life=hl,
            intercept=float(intercept),
            r_squared=r2,
            adj_r_squared=adj_r2,
            n_points=len(sel_t),
            time_start=float(sel_t[0]),
            time_end=float(sel_t[-1]),
            selected_times=sel_t.tolist(),
            selected_concs=sel_c.tolist(),
            method="manual",
            warnings=lz_warnings,
        )

    else:
        raise ValueError(f"Unknown method {method!r}. Use 'auto' or 'manual'.")


# ---------------------------------------------------------------------------
# AUC extrapolation and PK parameters
# ---------------------------------------------------------------------------


def auc_inf_obs(
    auclast: float,
    clast_obs: float,
    lambda_z_result: LambdaZResult,
) -> float:
    """Compute AUC extrapolated to infinity using the last observed concentration.

    Parameters
    ----------
    auclast : float
        AUC from time 0 to the last quantifiable time point.
    clast_obs : float
        Last observed (quantifiable) concentration.
    lambda_z_result : LambdaZResult
        Result from lambda_z(), providing the terminal rate constant.

    Returns
    -------
    float
        AUCinf_obs = AUClast + Clast_obs / lambda_z.

    Raises
    ------
    ValueError
        If lambda_z <= 0 or clast_obs < 0.
    """
    if lambda_z_result.lambda_z <= 0.0:
        raise ValueError(
            f"lambda_z must be positive (got {lambda_z_result.lambda_z})."
        )
    if clast_obs < 0.0:
        raise ValueError(
            f"clast_obs must be >= 0 (got {clast_obs})."
        )
    return auclast + clast_obs / lambda_z_result.lambda_z


def auc_percent_extrapolated(auclast: float, aucinf: float) -> float:
    """Compute the percentage of AUCinf that is extrapolated beyond the last time point.

    Parameters
    ----------
    auclast : float
        AUC from time 0 to the last quantifiable time point.
    aucinf : float
        AUC extrapolated to infinity.

    Returns
    -------
    float
        100 * (AUCinf - AUClast) / AUCinf.

    Raises
    ------
    ValueError
        If aucinf <= 0.
    """
    if aucinf <= 0.0:
        raise ValueError(
            f"aucinf must be positive (got {aucinf}); percent extrapolated is undefined."
        )
    return 100.0 * (aucinf - auclast) / aucinf


def clearance_volume_parameters(
    dose: float,
    aucinf: float,
    lambda_z_result: LambdaZResult,
    *,
    route: Literal["oral", "iv_bolus", "iv_infusion"],
) -> dict[str, float]:
    """Compute apparent or absolute clearance and volume of distribution.

    Parameters
    ----------
    dose : float
        Administered dose (same units as concentration * time in AUC).
    aucinf : float
        AUC extrapolated to infinity.
    lambda_z_result : LambdaZResult
        Result from lambda_z(), providing the terminal rate constant.
    route : {"oral", "iv_bolus", "iv_infusion"}
        Route of administration. Oral returns apparent parameters (CL_F, Vz_F);
        IV routes return absolute parameters (CL, Vz).

    Returns
    -------
    dict[str, float]
        For oral: {"CL_F": ..., "Vz_F": ...}.
        For iv_bolus or iv_infusion: {"CL": ..., "Vz": ...}.

    Raises
    ------
    ValueError
        If route is invalid, aucinf <= 0, or lambda_z <= 0.
    """
    valid_routes = ("oral", "iv_bolus", "iv_infusion")
    if route not in valid_routes:
        raise ValueError(
            f"route must be one of {valid_routes!r} (got {route!r})."
        )
    if aucinf <= 0.0:
        raise ValueError(
            f"aucinf must be positive (got {aucinf})."
        )
    if lambda_z_result.lambda_z <= 0.0:
        raise ValueError(
            f"lambda_z must be positive (got {lambda_z_result.lambda_z})."
        )

    lz = lambda_z_result.lambda_z
    if route == "oral":
        return {
            "CL_F": dose / aucinf,
            "Vz_F": dose / (aucinf * lz),
        }
    else:
        return {
            "CL": dose / aucinf,
            "Vz": dose / (aucinf * lz),
        }
