"""IVIVC Level B and Level C correlation helpers.

Level B correlates mean in vitro dissolution time (MDT) with mean in vivo
residence time (MRT). Level C correlates a single dissolution metric with a
single PK metric via linear regression.

References
----------
FDA Guidance for Industry: Extended Release Oral Dosage Forms: Development,
Evaluation, and Application of In Vitro/In Vivo Correlations (1997). CDER.

Gibaldi, M., & Perrier, D. (1982). Pharmacokinetics (2nd ed.). Marcel Dekker.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class LinearCorrelationResult:
    """Linear regression summary for Level B / Level C IVIVC.

    Parameters
    ----------
    slope : float
        Ordinary least-squares slope.
    intercept : float
        Ordinary least-squares intercept.
    r : float
        Pearson correlation coefficient.
    r_squared : float
        Coefficient of determination.
    n : int
        Number of paired observations used.
    """

    slope: float
    intercept: float
    r: float
    r_squared: float
    n: int


def _validate_pairs(
    x: Sequence[float] | np.ndarray,
    y: Sequence[float] | np.ndarray,
    *,
    x_name: str,
    y_name: str,
    min_points: int = 2,
) -> tuple[np.ndarray, np.ndarray]:
    """Validate equal-length finite arrays for correlation."""
    xa = np.asarray(x, dtype=float)
    ya = np.asarray(y, dtype=float)
    if xa.ndim != 1 or ya.ndim != 1:
        raise ValueError(f"{x_name} and {y_name} must be 1-D sequences.")
    if len(xa) != len(ya):
        raise ValueError(
            f"{x_name} and {y_name} must have the same length (got {len(xa)} and {len(ya)})."
        )
    if len(xa) < min_points:
        raise ValueError(f"At least {min_points} paired points required (got {len(xa)}).")
    if not np.all(np.isfinite(xa)) or not np.all(np.isfinite(ya)):
        raise ValueError(f"{x_name} and {y_name} must be finite (no NaN or inf).")
    return xa, ya


def _linear_correlation(
    x: Sequence[float] | np.ndarray,
    y: Sequence[float] | np.ndarray,
    *,
    x_name: str,
    y_name: str,
) -> LinearCorrelationResult:
    """OLS linear regression with Pearson r and R-squared."""
    xa, ya = _validate_pairs(x, y, x_name=x_name, y_name=y_name, min_points=2)
    slope, intercept = np.polyfit(xa, ya, 1)
    y_hat = slope * xa + intercept
    ss_res = float(np.sum((ya - y_hat) ** 2))
    ss_tot = float(np.sum((ya - np.mean(ya)) ** 2))
    if ss_tot <= 0.0:
        r_squared = 1.0 if ss_res <= 0.0 else 0.0
        r = 0.0
    else:
        r_squared = 1.0 - ss_res / ss_tot
        # Pearson r with sign of slope
        r = float(np.corrcoef(xa, ya)[0, 1])
        if not np.isfinite(r):
            r = 0.0
    return LinearCorrelationResult(
        slope=float(slope),
        intercept=float(intercept),
        r=float(r),
        r_squared=float(r_squared),
        n=int(len(xa)),
    )


def mean_dissolution_time(
    times: Sequence[float] | np.ndarray,
    fraction_dissolved: Sequence[float] | np.ndarray,
) -> float:
    """Mean dissolution time (MDT) via trapezoidal moment formula.

    Uses cumulative fraction (or percent) dissolved and the first statistical
    moment of the dissolution rate::

        MDT = (sum_i t_mid_i * dQ_i) / Q_last

    where ``t_mid_i = (t_i + t_{i-1}) / 2`` and ``dQ_i = Q_i - Q_{i-1}``.

    Parameters
    ----------
    times : Sequence[float]
        Dissolution sampling times (strictly increasing, same units throughout).
    fraction_dissolved : Sequence[float]
        Cumulative amount, fraction, or percent dissolved at each time.
        Must be non-decreasing and non-negative. Scale cancels in the ratio.

    Returns
    -------
    float
        Mean dissolution time in the same time units as ``times``.

    Raises
    ------
    ValueError
        If arrays mismatch, have fewer than 2 points, are non-finite, times
        are not strictly increasing, fractions are negative or decreasing,
        or final dissolved amount is zero.

    Notes
    -----
    Equivalent to AUMC_diss / AUC_diss of the differential dissolution rate
    under a piecewise-constant rate assumption between sampling times.

    References
    ----------
    FDA Guidance for Industry: Extended Release Oral Dosage Forms (1997). CDER.
    Gibaldi, M., & Perrier, D. (1982). Pharmacokinetics (2nd ed.). Marcel Dekker.
    """
    t = np.asarray(times, dtype=float)
    q = np.asarray(fraction_dissolved, dtype=float)
    if t.ndim != 1 or q.ndim != 1:
        raise ValueError("times and fraction_dissolved must be 1-D sequences.")
    if len(t) != len(q):
        raise ValueError(
            f"times and fraction_dissolved must have the same length (got {len(t)} and {len(q)})."
        )
    if len(t) < 2:
        raise ValueError(f"At least 2 time points required for MDT (got {len(t)}).")
    if not np.all(np.isfinite(t)) or not np.all(np.isfinite(q)):
        raise ValueError("times and fraction_dissolved must be finite (no NaN or inf).")
    if np.any(np.diff(t) <= 0.0):
        raise ValueError("times must be strictly increasing.")
    if np.any(q < 0.0):
        raise ValueError("fraction_dissolved must be non-negative.")
    # Allow tiny numerical decreases; reject clear non-monotonicity
    dq = np.diff(q)
    if np.any(dq < -1e-12 * max(1.0, float(np.max(np.abs(q))))):
        raise ValueError("fraction_dissolved must be non-decreasing.")
    dq = np.maximum(dq, 0.0)
    q_last = float(q[-1])
    if q_last <= 0.0:
        raise ValueError("Final fraction_dissolved must be > 0 to compute MDT.")

    t_mid = 0.5 * (t[1:] + t[:-1])
    mdt = float(np.sum(t_mid * dq) / q_last)
    return mdt


def mean_residence_time(
    times: Sequence[float] | np.ndarray,
    concentrations: Sequence[float] | np.ndarray,
) -> float:
    """Mean residence time (MRT) = AUMC / AUC (linear trapezoidal).

    Parameters
    ----------
    times : Sequence[float]
        Plasma sampling times (strictly increasing).
    concentrations : Sequence[float]
        Plasma concentrations at each time (non-negative).

    Returns
    -------
    float
        MRT in the same time units as ``times`` (AUMC_last / AUC_last).
        This is the truncated (to last sample) moment ratio; terminal
        extrapolation is not applied.

    Raises
    ------
    ValueError
        If arrays mismatch, have fewer than 2 points, are non-finite, times
        are not strictly increasing, concentrations are negative, or AUC is 0.

    Notes
    -----
    AUC = integral C dt, AUMC = integral t*C dt, both via linear trapezoids
    from the first to the last observed time point.

    References
    ----------
    Gibaldi, M., & Perrier, D. (1982). Pharmacokinetics (2nd ed.), Chapter 11.
    FDA Guidance for Industry: Extended Release Oral Dosage Forms (1997). CDER.
    """
    t = np.asarray(times, dtype=float)
    c = np.asarray(concentrations, dtype=float)
    if t.ndim != 1 or c.ndim != 1:
        raise ValueError("times and concentrations must be 1-D sequences.")
    if len(t) != len(c):
        raise ValueError(
            f"times and concentrations must have the same length (got {len(t)} and {len(c)})."
        )
    if len(t) < 2:
        raise ValueError(f"At least 2 time points required for MRT (got {len(t)}).")
    if not np.all(np.isfinite(t)) or not np.all(np.isfinite(c)):
        raise ValueError("times and concentrations must be finite (no NaN or inf).")
    if np.any(np.diff(t) <= 0.0):
        raise ValueError("times must be strictly increasing.")
    if np.any(c < 0.0):
        raise ValueError("concentrations must be non-negative.")

    dt = np.diff(t)
    # Linear trapezoidal AUC
    auc = float(np.sum(dt * (c[:-1] + c[1:]) / 2.0))
    if auc <= 0.0:
        raise ValueError("AUC is <= 0; cannot compute MRT.")

    # Linear trapezoidal AUMC of t*C
    tc = t * c
    aumc = float(np.sum(dt * (tc[:-1] + tc[1:]) / 2.0))
    return aumc / auc


def level_b_correlation(
    mdt_values: Sequence[float] | np.ndarray,
    mrt_values: Sequence[float] | np.ndarray,
) -> LinearCorrelationResult:
    """Level B IVIVC: linear correlation of MDT (in vitro) vs MRT (in vivo).

    Parameters
    ----------
    mdt_values : Sequence[float]
        Mean dissolution times for each formulation (in vitro).
    mrt_values : Sequence[float]
        Mean residence times for the same formulations (in vivo).

    Returns
    -------
    LinearCorrelationResult
        OLS slope, intercept, Pearson r, and R-squared.

    Raises
    ------
    ValueError
        If arrays are invalid for regression (see ``_linear_correlation``).

    References
    ----------
    FDA Guidance for Industry: Extended Release Oral Dosage Forms (1997). CDER.
    Section on Level B correlations (MDT vs MRT).
    """
    return _linear_correlation(
        mdt_values,
        mrt_values,
        x_name="mdt_values",
        y_name="mrt_values",
    )


def level_c_correlation(
    dissolution_metric: Sequence[float] | np.ndarray,
    pk_metric: Sequence[float] | np.ndarray,
) -> LinearCorrelationResult:
    """Level C IVIVC: linear correlation of one dissolution metric vs one PK metric.

    Typical pairs: percent dissolved at a fixed time vs Cmax or AUC; MDT vs
    Tmax; etc. The caller supplies already-computed metric vectors.

    Parameters
    ----------
    dissolution_metric : Sequence[float]
        In vitro metric values (one per formulation or condition).
    pk_metric : Sequence[float]
        Matching in vivo PK metric values.

    Returns
    -------
    LinearCorrelationResult
        OLS slope, intercept, Pearson r, and R-squared.

    Raises
    ------
    ValueError
        If arrays are invalid for regression (see ``_linear_correlation``).

    References
    ----------
    FDA Guidance for Industry: Extended Release Oral Dosage Forms (1997). CDER.
    Section on Level C correlations (point-to-point metric correlation).
    """
    return _linear_correlation(
        dissolution_metric,
        pk_metric,
        x_name="dissolution_metric",
        y_name="pk_metric",
    )
