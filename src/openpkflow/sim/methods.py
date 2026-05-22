"""Pure-math PK simulation functions: analytical concentration-time equations.

No file I/O, no pandas, no matplotlib. All inputs are plain Python sequences or numpy arrays.
Analytical solutions for 1- and 2-compartment models (IV bolus, IV infusion, oral).
"""

from __future__ import annotations

import math
from collections.abc import Callable

import numpy as np

# ---------------------------------------------------------------------------
# Shared validation helpers
# ---------------------------------------------------------------------------


def _validate_positive(**kwargs: float) -> None:
    for name, val in kwargs.items():
        if val <= 0.0:
            raise ValueError(f"{name} must be > 0 (got {val}).")


def _validate_nonneg(**kwargs: float) -> None:
    for name, val in kwargs.items():
        if val < 0.0:
            raise ValueError(f"{name} must be >= 0 (got {val}).")


def _prepare_times(times: list[float] | np.ndarray) -> np.ndarray:
    """Return a validated, float64 1-D time array.

    Parameters
    ----------
    times : array-like
        Simulation time points.

    Returns
    -------
    np.ndarray
        Validated float64 array.

    Raises
    ------
    ValueError
        If times is empty, contains negatives, or is not strictly increasing.
    """
    t = np.asarray(times, dtype=float)
    if t.ndim != 1 or len(t) == 0:
        raise ValueError("times must be a non-empty 1-D array.")
    if np.any(t < 0.0):
        raise ValueError("times must all be >= 0.")
    if len(t) > 1 and not np.all(np.diff(t) > 0.0):
        raise ValueError("times must be strictly increasing.")
    return t


# ---------------------------------------------------------------------------
# 1-compartment models
# ---------------------------------------------------------------------------


def c_1cmt_iv_bolus(
    times: list[float] | np.ndarray,
    dose: float,
    CL: float,
    Vz: float,
) -> np.ndarray:
    """Simulate a 1-compartment IV bolus concentration-time profile.

    Parameters
    ----------
    times : array-like
        Simulation time points (>= 0, strictly increasing).
    dose : float
        Dose amount.
    CL : float
        Systemic clearance (absolute, IV route). Must be > 0.
    Vz : float
        Volume of distribution at terminal phase. Must be > 0.

    Returns
    -------
    np.ndarray
        Concentration at each time point.

    Raises
    ------
    ValueError
        If CL or Vz <= 0, dose < 0, or times are invalid.

    Notes
    -----
    C(t) = (D/Vz) * exp(-k*t), where k = CL/Vz.
    Reference: Gibaldi & Perrier, Pharmacokinetics 2nd ed. (1982), Eq. 1-2, p. 2.
    """
    _validate_positive(CL=CL, Vz=Vz)
    _validate_nonneg(dose=dose)
    t = _prepare_times(times)
    k = CL / Vz
    return (dose / Vz) * np.exp(-k * t)


def c_1cmt_iv_infusion(
    times: list[float] | np.ndarray,
    dose: float,
    CL: float,
    Vz: float,
    t_inf: float,
) -> np.ndarray:
    """Simulate a 1-compartment constant-rate IV infusion concentration-time profile.

    Parameters
    ----------
    times : array-like
        Simulation time points (>= 0, strictly increasing).
    dose : float
        Total dose amount infused over t_inf.
    CL : float
        Systemic clearance (absolute, IV route). Must be > 0.
    Vz : float
        Volume of distribution at terminal phase. Must be > 0.
    t_inf : float
        Infusion duration (same time units as times). Must be > 0.

    Returns
    -------
    np.ndarray
        Concentration at each time point.

    Raises
    ------
    ValueError
        If CL, Vz, or t_inf <= 0, dose < 0, or times are invalid.

    Notes
    -----
    R0 = dose/t_inf (zero-order infusion rate), k = CL/Vz.
    During infusion (t <= t_inf): C(t) = (R0/CL) * (1 - exp(-k*t)).
    After infusion (t > t_inf): C(t) = (R0/CL) * (1 - exp(-k*t_inf)) * exp(-k*(t-t_inf)).
    Reference: Gibaldi & Perrier, Pharmacokinetics 2nd ed. (1982), Eq. 2-1, p. 44.
    """
    _validate_positive(CL=CL, Vz=Vz, t_inf=t_inf)
    _validate_nonneg(dose=dose)
    t = _prepare_times(times)
    k = CL / Vz
    R0 = dose / t_inf

    during = t <= t_inf
    C = np.empty_like(t)
    C[during] = (R0 / CL) * (1.0 - np.exp(-k * t[during]))
    C_peak = (R0 / CL) * (1.0 - np.exp(-k * t_inf))
    C[~during] = C_peak * np.exp(-k * (t[~during] - t_inf))
    return C


def c_1cmt_oral(
    times: list[float] | np.ndarray,
    dose: float,
    CL_F: float,
    Vz_F: float,
    ka: float,
) -> np.ndarray:
    """Simulate a 1-compartment first-order oral absorption concentration-time profile.

    Parameters
    ----------
    times : array-like
        Simulation time points (>= 0, strictly increasing).
    dose : float
        Nominal dose amount (bioavailability is absorbed into CL_F and Vz_F).
    CL_F : float
        Apparent oral clearance (CL/F). Must be > 0.
    Vz_F : float
        Apparent volume of distribution (Vz/F). Must be > 0.
    ka : float
        First-order absorption rate constant. Must be > 0.

    Returns
    -------
    np.ndarray
        Concentration at each time point.

    Raises
    ------
    ValueError
        If CL_F, Vz_F, or ka <= 0, dose < 0, or times are invalid.

    Notes
    -----
    k = CL_F/Vz_F. General (Bateman) case:
    C(t) = D*ka / (Vz_F*(ka-k)) * (exp(-k*t) - exp(-ka*t)).
    Flip-flop limit (ka == k, L'Hopital): C(t) = (D*k/Vz_F) * t * exp(-k*t).
    Reference: Gibaldi & Perrier, Pharmacokinetics 2nd ed. (1982), Eq. 1-13, p. 16.
    """
    _validate_positive(CL_F=CL_F, Vz_F=Vz_F, ka=ka)
    _validate_nonneg(dose=dose)
    t = _prepare_times(times)
    k = CL_F / Vz_F

    if math.isclose(ka, k, rel_tol=1e-6):
        return (dose * k / Vz_F) * t * np.exp(-k * t)
    return (dose * ka / (Vz_F * (ka - k))) * (np.exp(-k * t) - np.exp(-ka * t))


# ---------------------------------------------------------------------------
# 2-compartment models
# ---------------------------------------------------------------------------


def _2cmt_macro_constants(k10: float, k12: float, k21: float) -> tuple[float, float]:
    """Compute macro-constants alpha and beta for a 2-compartment model.

    Parameters
    ----------
    k10 : float
        Elimination micro-rate constant from central.
    k12 : float
        Transfer micro-rate from central to peripheral.
    k21 : float
        Transfer micro-rate from peripheral to central.

    Returns
    -------
    tuple[float, float]
        (alpha, beta) with alpha > beta > 0.
    """
    s1 = k10 + k12 + k21
    disc = math.sqrt(s1 * s1 - 4.0 * k10 * k21)
    alpha = (s1 + disc) / 2.0
    beta = (s1 - disc) / 2.0
    return alpha, beta


def c_2cmt_iv_bolus(
    times: list[float] | np.ndarray,
    dose: float,
    CL: float,
    V1: float,
    Q: float,
    V2: float,
) -> np.ndarray:
    """Simulate a 2-compartment IV bolus concentration-time profile.

    Parameters
    ----------
    times : array-like
        Simulation time points (>= 0, strictly increasing).
    dose : float
        Dose amount (absolute).
    CL : float
        Systemic clearance from central compartment. Must be > 0.
    V1 : float
        Central compartment volume. Must be > 0.
    Q : float
        Intercompartmental clearance. Must be > 0.
    V2 : float
        Peripheral compartment volume. Must be > 0.

    Returns
    -------
    np.ndarray
        Concentration in the central compartment at each time point.

    Raises
    ------
    ValueError
        If any rate parameter <= 0, dose < 0, or times are invalid.

    Notes
    -----
    k10 = CL/V1, k12 = Q/V1, k21 = Q/V2.
    C(t) = A*exp(-alpha*t) + B*exp(-beta*t), A + B = D/V1.
    Reference: Gibaldi & Perrier, Pharmacokinetics 2nd ed. (1982), Eq. 3-1, p. 62.
    """
    _validate_positive(CL=CL, V1=V1, Q=Q, V2=V2)
    _validate_nonneg(dose=dose)
    t = _prepare_times(times)

    k10 = CL / V1
    k12 = Q / V1
    k21 = Q / V2
    alpha, beta = _2cmt_macro_constants(k10, k12, k21)

    A = (dose / V1) * (alpha - k21) / (alpha - beta)
    B = (dose / V1) * (k21 - beta) / (alpha - beta)
    return A * np.exp(-alpha * t) + B * np.exp(-beta * t)


def c_2cmt_iv_infusion(
    times: list[float] | np.ndarray,
    dose: float,
    CL: float,
    V1: float,
    Q: float,
    V2: float,
    t_inf: float,
) -> np.ndarray:
    """Simulate a 2-compartment constant-rate IV infusion concentration-time profile.

    Parameters
    ----------
    times : array-like
        Simulation time points (>= 0, strictly increasing).
    dose : float
        Total dose amount infused over t_inf.
    CL : float
        Systemic clearance from central compartment. Must be > 0.
    V1 : float
        Central compartment volume. Must be > 0.
    Q : float
        Intercompartmental clearance. Must be > 0.
    V2 : float
        Peripheral compartment volume. Must be > 0.
    t_inf : float
        Infusion duration (same time units as times). Must be > 0.

    Returns
    -------
    np.ndarray
        Concentration in the central compartment at each time point.

    Raises
    ------
    ValueError
        If any rate parameter <= 0, dose < 0, t_inf <= 0, or times are invalid.

    Notes
    -----
    k10 = CL/V1, k12 = Q/V1, k21 = Q/V2.
    R0 = dose/t_inf. A_s = (alpha-k21)/(V1*(alpha-beta)), B_s = (k21-beta)/(V1*(alpha-beta)).
    During infusion: C(t) = R0 * [A_s/alpha*(1-exp(-alpha*t)) + B_s/beta*(1-exp(-beta*t))].
    After infusion: each term decays from its end-of-infusion value.
    Derived by convolving the 2-cmt bolus impulse response with a rectangular pulse.
    Reference: Gibaldi & Perrier, Pharmacokinetics 2nd ed. (1982), Eqs. 3-28 to 3-30, p. 75.
    """
    _validate_positive(CL=CL, V1=V1, Q=Q, V2=V2, t_inf=t_inf)
    _validate_nonneg(dose=dose)
    t = _prepare_times(times)

    k10 = CL / V1
    k12 = Q / V1
    k21 = Q / V2
    alpha, beta = _2cmt_macro_constants(k10, k12, k21)
    R0 = dose / t_inf

    A_s = (alpha - k21) / (V1 * (alpha - beta))
    B_s = (k21 - beta) / (V1 * (alpha - beta))

    during = t <= t_inf
    C = np.empty_like(t)

    t_d = t[during]
    C[during] = R0 * (
        A_s / alpha * (1.0 - np.exp(-alpha * t_d)) + B_s / beta * (1.0 - np.exp(-beta * t_d))
    )

    t_p = t[~during]
    C[~during] = R0 * (
        A_s / alpha * (1.0 - np.exp(-alpha * t_inf)) * np.exp(-alpha * (t_p - t_inf))
        + B_s / beta * (1.0 - np.exp(-beta * t_inf)) * np.exp(-beta * (t_p - t_inf))
    )

    return C


def c_2cmt_oral(
    times: list[float] | np.ndarray,
    dose: float,
    CL_F: float,
    V1_F: float,
    Q: float,
    V2: float,
    ka: float,
) -> np.ndarray:
    """Simulate a 2-compartment oral absorption concentration-time profile.

    Parameters
    ----------
    times : array-like
        Simulation time points (>= 0, strictly increasing).
    dose : float
        Nominal dose amount (bioavailability absorbed into CL_F and V1_F).
    CL_F : float
        Apparent systemic clearance (CL/F). Must be > 0.
    V1_F : float
        Apparent central compartment volume (V1/F). Must be > 0.
    Q : float
        Intercompartmental clearance. Must be > 0.
    V2 : float
        Peripheral compartment volume. Must be > 0.
    ka : float
        First-order absorption rate constant. Must be > 0.

    Returns
    -------
    np.ndarray
        Concentration in the central compartment at each time point.

    Raises
    ------
    ValueError
        If any rate parameter <= 0, dose < 0, times are invalid, or ka
        is numerically equal to alpha or beta (degenerate analytical form).

    Notes
    -----
    k10 = CL_F/V1_F, k12 = Q/V1_F, k21 = Q/V2.
    C(t) = (D*ka/V1_F) * [A*exp(-alpha*t) + B*exp(-beta*t) + C*exp(-ka*t)].
    Reference: Gibaldi & Perrier, Pharmacokinetics 2nd ed. (1982), Eq. 4-4, p. 99.
    """
    _validate_positive(CL_F=CL_F, V1_F=V1_F, Q=Q, V2=V2, ka=ka)
    _validate_nonneg(dose=dose)
    t = _prepare_times(times)

    k10 = CL_F / V1_F
    k12 = Q / V1_F
    k21 = Q / V2
    alpha, beta = _2cmt_macro_constants(k10, k12, k21)

    _EPS = 1e-9
    if abs(ka - alpha) < _EPS or abs(ka - beta) < _EPS:
        raise ValueError(
            f"ka ({ka:.6g}) is numerically equal to alpha ({alpha:.6g}) or "
            f"beta ({beta:.6g}). The analytical 2-cmt oral solution is undefined "
            "at this point; adjust ka or model parameters."
        )

    coeff_alpha = (k21 - alpha) / ((beta - alpha) * (ka - alpha))
    coeff_beta = (k21 - beta) / ((alpha - beta) * (ka - beta))
    coeff_ka = (k21 - ka) / ((alpha - ka) * (beta - ka))

    return (dose * ka / V1_F) * (
        coeff_alpha * np.exp(-alpha * t)
        + coeff_beta * np.exp(-beta * t)
        + coeff_ka * np.exp(-ka * t)
    )


# ---------------------------------------------------------------------------
# Superposition for repeated dosing
# ---------------------------------------------------------------------------


def superpose(
    times: np.ndarray,
    dose_times: list[float],
    dose_amounts: list[float],
    unit_fn: Callable[[np.ndarray, float], np.ndarray],
) -> np.ndarray:
    """Sum single-dose contributions for a linear multi-dose regimen.

    Parameters
    ----------
    times : np.ndarray
        Absolute simulation time grid (>= 0, strictly increasing).
    dose_times : list[float]
        Time of each dose administration.
    dose_amounts : list[float]
        Dose amount for each administration.
    unit_fn : callable
        ``(t_relative, dose_amount) -> np.ndarray``. Returns the concentration
        profile for a single dose of ``dose_amount`` given at t=0, evaluated at
        the relative times ``t_relative``.

    Returns
    -------
    np.ndarray
        Total concentration at each time point.

    Notes
    -----
    Valid only for linear (first-order) PK systems. Assumes each dose
    contributes independently — superposition breaks for nonlinear elimination.
    """
    t = np.asarray(times, dtype=float)
    C_total = np.zeros_like(t)
    for t_dose, amount in zip(dose_times, dose_amounts, strict=True):
        t_rel = t - t_dose
        mask = t_rel >= 0.0
        if mask.any():
            C_total[mask] += unit_fn(t_rel[mask], amount)
    return C_total
