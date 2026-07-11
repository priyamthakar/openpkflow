"""IVIVC Level A: deconvolution, convolution, Levy plot, predictability.

References
----------
FDA Guidance for Industry: Extended Release Oral Dosage Forms: Development,
Evaluation, and Application of In Vitro/In Vivo Correlations (1997). CDER.

Wagner, J. G., & Nelson, E. (1963). Percentage absorbed-time plots derived from
blood level and urinary excretion data. Journal of Pharmaceutical Sciences,
52(6), 610-611. DOI: 10.1002/jps.2600520624

Loo, J. C. K., & Riegelman, S. (1968). New method for calculating the intrinsic
absorption rate of drugs. Journal of Pharmaceutical Sciences, 57(6), 918-928.
DOI: 10.1002/jps.2600570602

Gibaldi, M., & Perrier, D. (1982). Pharmacokinetics (2nd ed.). Marcel Dekker.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def _trapz_linear(
    times: np.ndarray | Sequence[float], values: np.ndarray | Sequence[float]
) -> np.ndarray:
    """Cumulative trapezoidal AUC via the linear method for ascending time."""
    t = np.asarray(times, dtype=float)
    v = np.asarray(values, dtype=float)
    dt = np.diff(t)
    avg = (v[:-1] + v[1:]) / 2.0
    cumsum = np.cumsum(dt * avg)
    return np.concatenate(([0.0], cumsum))


def wagner_nelson(
    times: Sequence[float] | np.ndarray,
    concentrations: Sequence[float] | np.ndarray,
    *,
    kel: float | None = None,
    iv_unit_impulse_times: Sequence[float] | np.ndarray | None = None,
    iv_unit_impulse_concs: Sequence[float] | np.ndarray | None = None,
) -> np.ndarray:
    """Wagner-Nelson deconvolution for one-compartment oral data.

    Computes the cumulative fraction absorbed versus time from plasma
    concentration data.  Requires either a terminal elimination rate
    constant `kel` or a unit impulse response (UIR) from IV bolus data
    to estimate kel internally.

    Parameters
    ----------
    times : Sequence[float]
        Plasma sampling times after oral administration, hours.
        Must be strictly increasing and start near zero.
    concentrations : Sequence[float]
        Plasma concentrations at each time point, same length as `times`.
    kel : float or None, optional
        Terminal elimination rate constant (1/h).  If None, estimated from
        a unit impulse response (IV bolus data).
    iv_unit_impulse_times : Sequence[float] or None, optional
        IV bolus sampling times for UIR; required if `kel` is None.
    iv_unit_impulse_concs : Sequence[float] or None, optional
        IV bolus concentrations; required if `kel` is None.

    Returns
    -------
    np.ndarray
        Cumulative fraction absorbed (F_a) at each time point, shape (n,).
        Values range from 0 to approximately 1.

    Raises
    ------
    ValueError
        If times and concentrations have mismatched lengths, fewer than 3
        points, non-finite values, or negative concentrations.

    Notes
    -----
    The Wagner-Nelson equation is::

        F_a(t) = [C(t) + kel * AUC_0^t] / [kel * AUC_0^inf]

    where AUC_0^t uses linear trapezoidal and AUC_0^inf = AUC_last + C_last/kel.

    References
    ----------
    Wagner & Nelson (1963), DOI: 10.1002/jps.2600520624
    Gibaldi & Perrier (1982), Pharmacokinetics, 2nd ed., Chapter 4.
    """
    t = np.asarray(times, dtype=float)
    c = np.asarray(concentrations, dtype=float)

    if len(t) != len(c):
        raise ValueError(
            f"times and concentrations must have the same length (got {len(t)} and {len(c)})"
        )
    if len(t) < 3:
        raise ValueError(f"At least 3 time points required for Wagner-Nelson (got {len(t)})")
    if not np.all(np.isfinite(c)):
        raise ValueError("Concentrations must be finite (no NaN or inf)")
    if np.any(c < 0):
        raise ValueError("Concentrations must be non-negative")

    # Determine kel: use provided value or estimate from IV UIR
    if kel is not None:
        if kel <= 0:
            raise ValueError(f"kel must be positive (got {kel})")
        _kel = float(kel)
    elif iv_unit_impulse_times is not None and iv_unit_impulse_concs is not None:
        iv_t = np.asarray(iv_unit_impulse_times, dtype=float)
        iv_c = np.asarray(iv_unit_impulse_concs, dtype=float)
        # Estimate kel from terminal log-linear portion (last 3+ points)
        n_term = min(len(iv_t), 4)
        if n_term < 3:
            raise ValueError("IV UIR data must have at least 3 time points to estimate kel")
        log_c = np.log(np.maximum(iv_c[-n_term:], 1e-30))
        slope, _ = np.polyfit(iv_t[-n_term:], log_c, 1)
        _kel = -slope
    else:
        raise ValueError(
            "Either `kel` or both `iv_unit_impulse_times` and `iv_unit_impulse_concs` "
            "must be provided"
        )

    # AUC_0^t via linear trapezoidal
    auc_cum = _trapz_linear(t, c)

    # AUC_0^inf = AUClast + C_last / kel
    auc_inf = auc_cum[-1] + c[-1] / _kel

    if auc_inf <= 0:
        raise ValueError("Computed AUC_inf is <= 0; check your data or kel value")

    # F_a(t) = (C(t) + kel * AUC_0^t) / (kel * AUC_inf)
    f_a = (c + _kel * auc_cum) / (_kel * auc_inf)

    return np.asarray(f_a, dtype=float)


def loo_riegelman(
    times: Sequence[float] | np.ndarray,
    concentrations: Sequence[float] | np.ndarray,
    *,
    kel: float,
    k12: float,
    k21: float,
) -> np.ndarray:
    """Loo-Riegelman deconvolution for two-compartment oral data.

    Computes cumulative fraction absorbed for drugs described by a
    two-compartment model with first-order elimination from the central
    compartment.

    Parameters
    ----------
    times : Sequence[float]
        Plasma sampling times after oral administration, hours.
        Must be strictly increasing and start near zero.
    concentrations : Sequence[float]
        Plasma concentrations at each time point.
    kel : float
        Elimination rate constant from the central compartment (k10, 1/h).
    k12 : float
        Central-to-peripheral transfer rate constant (1/h).
    k21 : float
        Peripheral-to-central transfer rate constant (1/h).

    Returns
    -------
    np.ndarray
        Cumulative fraction absorbed (F_a) at each time point, shape (n,).

    Raises
    ------
    ValueError
        If times and concentrations have mismatched lengths, fewer than 3
        points, non-finite or negative concentrations, or non-positive
        rate constants.

    Notes
    -----
    The Loo-Riegelman equation is::

        F_a(t) = [C(t) + k10 * AUC_0^t + k12 * exp(-k21*t) * AUC_0^t^{k21}] /
                 [k10 * AUC_0^inf]

    where the "k21-AUC" integral uses the exponentially-weighted concentration.

    References
    ----------
    Loo & Riegelman (1968), DOI: 10.1002/jps.2600570602
    Gibaldi & Perrier (1982), Pharmacokinetics, 2nd ed., Chapter 4.
    """
    t = np.asarray(times, dtype=float)
    c = np.asarray(concentrations, dtype=float)

    if len(t) != len(c):
        raise ValueError(
            f"times and concentrations must have the same length (got {len(t)} and {len(c)})"
        )
    if len(t) < 3:
        raise ValueError(f"At least 3 time points required for Loo-Riegelman (got {len(t)})")
    if not np.all(np.isfinite(c)):
        raise ValueError("Concentrations must be finite (no NaN or inf)")
    if np.any(c < 0):
        raise ValueError("Concentrations must be non-negative")
    if kel <= 0 or k12 <= 0 or k21 <= 0:
        raise ValueError("Rate constants (kel, k12, k21) must all be positive")

    # Linear trapezoidal AUC_0^t
    auc_0t = _trapz_linear(t, c)

    # Exponentially-weighted concentration for k21-AUC term
    c_exp = c * np.exp(k21 * t)

    # Trapezoidal integral of c_exp
    auc_exp = _trapz_linear(t, c_exp)

    # AUC_inf = AUClast + C_last / k10
    auc_inf = auc_0t[-1] + c[-1] / kel

    if auc_inf <= 0:
        raise ValueError("Computed AUC_inf is <= 0; check your data or rate constants")

    # Numerator: C(t) + k10 * AUC_0^t + k12 * exp(-k21*t) * AUC_exp(t)
    num = c + kel * auc_0t + k12 * np.exp(-k21 * t) * auc_exp

    # Denominator: k10 * AUC_inf
    denom = kel * auc_inf

    fa = num / denom

    return np.asarray(fa, dtype=float)


def convolution_predict(
    dissolution_times: Sequence[float] | np.ndarray,
    dissolution_pct: Sequence[float] | np.ndarray,
    *,
    iv_unit_impulse_times: Sequence[float] | np.ndarray,
    iv_unit_impulse_concs: Sequence[float] | np.ndarray,
    dose_diss: float | None = None,
    dose_iv: float | None = None,
    dissolution_time_unit: str = "hours",
) -> tuple[np.ndarray, np.ndarray]:
    """Predict in vivo concentration-time profile via numerical convolution.

    Performs convolution of the in vitro dissolution profile (input rate)
    with the unit impulse response (UIR) from IV bolus data to predict
    the plasma concentration-time profile.

    Parameters
    ----------
    dissolution_times : Sequence[float]
        Time points for the in vitro dissolution profile.
    dissolution_pct : Sequence[float]
        Cumulative percent dissolved at each dissolution time point
        (0-100 scale). Incomplete profiles are NOT re-normalised to 100%.
    iv_unit_impulse_times : Sequence[float]
        IV bolus plasma sampling times in hours.
    iv_unit_impulse_concs : Sequence[float]
        IV bolus plasma concentrations at each UIR time.
    dose_diss : float or None, optional
        Dose administered in the dissolution formulation. Defaults to
        unity for relative prediction.
    dose_iv : float or None, optional
        Dose administered IV for UIR. Defaults to unity for relative
        prediction.
    dissolution_time_unit : {"hours", "minutes"}, optional
        Unit of ``dissolution_times``. Minutes are converted to hours so
        dissolution and UIR share a consistent time base. Default ``"hours"``.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        (predicted_times, predicted_concentrations) arrays in hours.

    Notes
    -----
    Convolution integral::

        C_pred(t) = dose_diss/dose_iv * integrate(R_in(tau) * UIR(t - tau), dtau, 0, t)

    where R_in is the dissolution input rate (derivative of cumulative
    dissolution fraction) and UIR is the unit impulse response.  The
    discretised convolution uses the trapezoidal approximation.
    """
    import numpy as np

    d_t = np.asarray(dissolution_times, dtype=float)
    d_pct = np.asarray(dissolution_pct, dtype=float)
    u_t = np.asarray(iv_unit_impulse_times, dtype=float)
    u_c = np.asarray(iv_unit_impulse_concs, dtype=float)

    unit = dissolution_time_unit.lower().strip()
    if unit in ("min", "mins", "minute", "minutes"):
        d_t = d_t / 60.0
    elif unit not in ("h", "hr", "hrs", "hour", "hours"):
        raise ValueError(
            f"dissolution_time_unit must be 'hours' or 'minutes' (got {dissolution_time_unit!r})."
        )

    dose_ratio = 1.0
    if dose_diss is not None and dose_iv is not None and dose_iv > 0:
        dose_ratio = dose_diss / dose_iv

    # Convert percent dissolved to fraction. Do NOT re-scale incomplete profiles
    # to 100% -- that invents mass that was never dissolved.
    if np.any(d_pct < 0) or np.any(d_pct > 100.0 + 1e-9):
        raise ValueError("dissolution_pct values must be in [0, 100].")
    max_pct = float(np.max(d_pct))
    if max_pct <= 0:
        raise ValueError("Dissolution profile must have positive values")
    d_frac = d_pct / 100.0

    # Create a uniform time grid spanning the combined range
    t_min = 0.0
    t_max = float(u_t[-1])
    if t_max <= 0:
        raise ValueError("UIR times must extend beyond 0.")
    positive_d = np.diff(d_t[d_t > 0]) if len(d_t) > 1 else np.array([])
    positive_u = np.diff(u_t[u_t > 0]) if len(u_t) > 1 else np.array([])
    dt = min(
        float(np.min(positive_d)) if len(positive_d) else 0.1,
        float(np.min(positive_u)) if len(positive_u) else 0.1,
        0.5,
    )
    dt = max(dt, 0.01)

    n_steps = int(t_max / dt) + 1
    t_grid = np.linspace(t_min, t_max, n_steps)

    # Interpolate UIR onto the uniform grid
    uir_interp = np.interp(t_grid, u_t, u_c, left=u_c[0], right=0.0)

    # Input rate: derivative of cumulative dissolution fraction
    d_interp = np.interp(t_grid, d_t, d_frac, left=0.0, right=d_frac[-1])
    input_rate = np.gradient(d_interp, dt, edge_order=2)
    input_rate = np.maximum(input_rate, 0.0)

    # Convolution via cumulative sum (discrete trapezoidal)
    conv = np.convolve(input_rate, uir_interp, mode="full")[:n_steps] * dt

    c_pred = conv * dose_ratio

    return t_grid, c_pred


def levy_plot_data(
    in_vitro_times: Sequence[float] | np.ndarray,
    in_vitro_fraction: Sequence[float] | np.ndarray,
    in_vivo_fraction: Sequence[float] | np.ndarray,
) -> dict[str, np.ndarray]:
    """Compute data for a Levy plot (IVIVC correlation plot).

    A Levy plot shows in vitro fraction dissolved against in vivo fraction
    absorbed at matched time points.  The slope indicates the deconvolution
    factor; values near 1.0 indicate a 1:1 IVIVC.

    Parameters
    ----------
    in_vitro_times : Sequence[float]
        Dissolution sampling times.
    in_vitro_fraction : Sequence[float]
        Cumulative fraction dissolved at each dissolution time point.
    in_vivo_fraction : Sequence[float]
        Cumulative fraction absorbed at each in vivo time point (from
        Wagner-Nelson or Loo-Riegelman).

    Returns
    -------
    dict[str, np.ndarray]
        Dictionary with keys:
        ``"x"`` -- in vitro fraction dissolved,
        ``"y"`` -- in vivo fraction absorbed,
        ``"slope"`` -- regression slope (scalar),
        ``"intercept"`` -- regression intercept (scalar),
        ``"r_squared"`` -- R-squared of the regression (scalar),
        ``"residuals"`` -- regression residuals.

    Notes
    -----
    F_a <= F_d for all matched points forms the basis for a valid IVIVC.
    """
    ivt = np.asarray(in_vitro_fraction, dtype=float)
    ivv = np.asarray(in_vivo_fraction, dtype=float)

    if len(ivt) != len(ivv):
        raise ValueError("in_vitro_fraction and in_vivo_fraction must be the same length")

    # Filter to values between 0.05 and 0.95 for robust regression
    mask = (ivt > 0.05) & (ivt < 0.95) & (ivv > 0.05) & (ivv < 0.95)
    if not np.any(mask):
        mask = np.ones_like(ivt, dtype=bool)

    x = ivt[mask]
    y = ivv[mask]

    if len(x) < 2:
        raise ValueError("At least 2 valid data points required for Levy plot regression")

    # Linear regression: y = slope * x + intercept
    slope, intercept = np.polyfit(x, y, 1)
    y_pred = slope * x + intercept
    residuals = y - y_pred
    ss_res = float(np.sum(residuals**2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r_squared = 1.0 - ss_res / max(ss_tot, 1e-30)

    return {
        "x": x,
        "y": y,
        "slope": float(slope),
        "intercept": float(intercept),
        "r_squared": float(r_squared),
        "residuals": residuals,
    }


def ivivc_predictability(
    observed_cmax: float,
    predicted_cmax: float,
    observed_auc: float,
    predicted_auc: float,
) -> dict[str, float | bool | str | None]:
    """FDA IVIVC percent prediction error (%PE) for one formulation.

    Computes %PE for Cmax and AUCinf separately. FDA evaluates internal
    predictability by averaging absolute %PE **across formulations for each
    metric** (Cmax and AUC separately), with formulation-level |%PE| <= 15%
    and cross-formulation mean absolute %PE <= 10% per metric. Averaging
    Cmax and AUC %PE within a single formulation is **not** the FDA criterion.

    This helper returns per-formulation %PE only. Regulatory pass/fail requires
    multi-formulation aggregation via :func:`ivivc_predictability_aggregate`.
    Single-formulation ``overall_pass`` is always ``None`` (not evaluated).

    Parameters
    ----------
    observed_cmax : float
        Observed (in vivo) Cmax for the formulation.
    predicted_cmax : float
        IVIVC-predicted Cmax.
    observed_auc : float
        Observed AUCinf for the formulation.
    predicted_auc : float
        IVIVC-predicted AUCinf.

    Returns
    -------
    dict
        ``%PE_Cmax``, ``%PE_AUC``, ``abs_%PE_Cmax``, ``abs_%PE_AUC``,
        ``formulation_cmax_within_15``, ``formulation_auc_within_15``,
        ``overall_pass`` (always None for single-formulation calls),
        and ``note``.

    References
    ----------
    FDA Guidance for Industry: Extended Release Oral Dosage Forms:
    Development, Evaluation, and Application of In Vitro/In Vivo Correlations
    (1997), Section V.B (Predictability).
    """
    if observed_cmax <= 0:
        raise ValueError(f"observed_cmax must be > 0 (got {observed_cmax}).")
    if observed_auc <= 0:
        raise ValueError(f"observed_auc must be > 0 (got {observed_auc}).")

    pe_cmax = ((predicted_cmax - observed_cmax) / observed_cmax) * 100.0
    pe_auc = ((predicted_auc - observed_auc) / observed_auc) * 100.0
    abs_cmax = abs(pe_cmax)
    abs_auc = abs(pe_auc)

    return {
        "%PE_Cmax": round(pe_cmax, 2),
        "%PE_AUC": round(pe_auc, 2),
        "abs_%PE_Cmax": round(abs_cmax, 2),
        "abs_%PE_AUC": round(abs_auc, 2),
        "formulation_cmax_within_15": abs_cmax <= 15.0,
        "formulation_auc_within_15": abs_auc <= 15.0,
        # Backward-compat keys: not FDA cross-formulation mean criteria
        "passes_cmax": abs_cmax <= 15.0,
        "passes_auc": abs_auc <= 15.0,
        "mean_abs_%PE": None,
        "passes_mean": None,
        "overall_pass": None,
        "note": (
            "Single-formulation %PE only. FDA internal predictability requires "
            "cross-formulation mean |%PE| <= 10% for Cmax and for AUC separately "
            "(not the average of Cmax and AUC within one formulation). "
            "Use ivivc_predictability_aggregate for multi-formulation verdicts."
        ),
    }


def ivivc_predictability_aggregate(
    formulation_results: Sequence[dict[str, float | bool | str | None]],
) -> dict[str, float | bool | str]:
    """Aggregate multi-formulation %PE using FDA internal predictability rules.

    Parameters
    ----------
    formulation_results : sequence of dict
        Outputs of :func:`ivivc_predictability` (one per formulation).

    Returns
    -------
    dict
        Cross-formulation mean absolute %PE for Cmax and AUC, whether each
        mean is <= 10%, whether every formulation is within 15% for each
        metric, and ``overall_pass``.

    References
    ----------
    FDA Guidance for Industry: Extended Release Oral Dosage Forms (1997),
    Section V.B.
    """
    if not formulation_results:
        raise ValueError("formulation_results must be non-empty.")

    abs_cmax = [float(r["abs_%PE_Cmax"]) for r in formulation_results]  # type: ignore[arg-type]
    abs_auc = [float(r["abs_%PE_AUC"]) for r in formulation_results]  # type: ignore[arg-type]
    mean_cmax = sum(abs_cmax) / len(abs_cmax)
    mean_auc = sum(abs_auc) / len(abs_auc)
    all_cmax_15 = all(bool(r["formulation_cmax_within_15"]) for r in formulation_results)
    all_auc_15 = all(bool(r["formulation_auc_within_15"]) for r in formulation_results)
    mean_cmax_ok = mean_cmax <= 10.0
    mean_auc_ok = mean_auc <= 10.0
    overall = all_cmax_15 and all_auc_15 and mean_cmax_ok and mean_auc_ok

    return {
        "n_formulations": len(formulation_results),
        "mean_abs_%PE_Cmax": round(mean_cmax, 2),
        "mean_abs_%PE_AUC": round(mean_auc, 2),
        "mean_cmax_within_10": mean_cmax_ok,
        "mean_auc_within_10": mean_auc_ok,
        "all_formulations_cmax_within_15": all_cmax_15,
        "all_formulations_auc_within_15": all_auc_15,
        "overall_pass": overall,
        "note": (
            "FDA internal predictability: for each of Cmax and AUC, mean |%PE| "
            "across formulations <= 10% and each formulation |%PE| <= 15%."
        ),
    }
