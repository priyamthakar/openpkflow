"""Student-friendly PK model fitting: fit 1-/2-compartment models to observed data.

Provides ``fit_pk_model()`` which accepts concentration-time arrays and fits
compartmental PK models using scipy.optimize.curve_fit.
"""

from __future__ import annotations

import math
import warnings
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import numpy as np
from scipy.optimize import OptimizeWarning, curve_fit

from openpkflow.sim.methods import c_1cmt_iv_bolus, c_1cmt_oral, c_2cmt_oral

# ---------------------------------------------------------------------------
# Thin wrappers around validated sim/methods.py functions for use with
# scipy curve_fit.  The validated functions raise ValueError on degenerate
# parameter combinations (e.g. ka == alpha); we catch those and return zeros
# so that curve_fit can step away from the degenerate region rather than
# aborting the optimisation.
# ---------------------------------------------------------------------------


def _oral_1cmt(t: np.ndarray, dose: float, CL_F: float, Vz_F: float, ka: float) -> np.ndarray:
    """Wrapper: 1-cmt oral, delegates to validated c_1cmt_oral."""
    try:
        return c_1cmt_oral(t, dose, CL_F, Vz_F, ka)
    except (ValueError, ZeroDivisionError):
        return np.zeros_like(t)


def _iv_1cmt(t: np.ndarray, dose: float, CL: float, Vz: float) -> np.ndarray:
    """Wrapper: 1-cmt IV bolus, delegates to validated c_1cmt_iv_bolus."""
    try:
        return c_1cmt_iv_bolus(t, dose, CL, Vz)
    except (ValueError, ZeroDivisionError):
        return np.zeros_like(t)


def _oral_2cmt(
    t: np.ndarray, dose: float, CL_F: float, V1_F: float, Q: float, V2: float, ka: float
) -> np.ndarray:
    """Wrapper: 2-cmt oral, delegates to validated c_2cmt_oral."""
    try:
        return c_2cmt_oral(t, dose, CL_F, V1_F, Q, V2, ka)
    except (ValueError, ZeroDivisionError):
        return np.zeros_like(t)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class PKModelFit:
    """Result of fitting a PK model to observed data.

    Attributes
    ----------
    model_type : str
        "1-compartment" or "2-compartment".
    route : str
        "oral" or "iv_bolus".
    params : dict[str, float]
        Fitted parameter values.
    param_se : dict[str, float]
        Standard errors of fitted parameters (delta method).
    r_squared : float
        Coefficient of determination.
    aic : float
        Akaike Information Criterion.
    converged : bool
        Whether the fit converged.
    observed_times : list[float]
        Input time points.
    observed_concs : list[float]
        Input concentrations.
    fitted_concs : list[float]
        Model-predicted concentrations at observed times.
    warnings : list[str]
        Fitting warnings.
    """

    model_type: str
    route: str
    params: dict[str, float]
    param_se: dict[str, float]
    r_squared: float
    aic: float
    converged: bool
    observed_times: list[float]
    observed_concs: list[float]
    fitted_concs: list[float]
    warnings: list[str] = field(default_factory=list)

    @property
    def half_life(self) -> float | None:
        """Terminal half-life from fitted parameters."""
        if not self.converged:
            return None
        if self.model_type == "1-compartment":
            if self.route == "oral":
                return math.log(2) / (self.params["CL_F"] / self.params["Vz_F"])
            return math.log(2) / (self.params["CL"] / self.params["Vz"])
        # 2-compartment: use beta (terminal phase)
        if "beta" in self.params:
            return math.log(2) / self.params["beta"]
        return None

    def summary(self) -> str:
        """Print a human-readable summary of the fit.

        Returns
        -------
        str
            Multi-line summary text.
        """
        lines: list[str] = []
        lines.append("-" * 55)
        lines.append(f"  {self.model_type.upper()} {self.route.upper()} MODEL FIT")
        lines.append("-" * 55)

        if not self.converged:
            lines.append("  FIT FAILED TO CONVERGE")
            lines.append("")
            return "\n".join(lines)

        lines.append(f"  R-squared: {self.r_squared:.6f}")
        lines.append(f"  AIC:       {self.aic:.2f}")
        if self.half_life is not None:
            lines.append(f"  Half-life: {self.half_life:.3f}")
        lines.append("")
        lines.append(f"  {'Parameter':<12} {'Estimate':>10} {'SE':>10} {'RSE%':>8}")
        lines.append("  " + "-" * 42)

        for name in self.params:
            val = self.params[name]
            se = self.param_se.get(name, float("nan"))
            rse = abs(se / val * 100) if val != 0 and not np.isnan(se) else float("nan")
            lines.append(f"  {name:<12} {val:>10.4f} {se:>10.4f} {rse:>8.1f}")

        if self.warnings:
            lines.append("")
            for w in self.warnings:
                lines.append(f"  WARNING: {w}")

        return "\n".join(lines)

    def predict(self, times: np.ndarray) -> np.ndarray:
        """Predict concentrations at new time points.

        Parameters
        ----------
        times : np.ndarray
            Time points at which to predict.

        Returns
        -------
        np.ndarray
            Predicted concentrations.

        Raises
        ------
        RuntimeError
            If the model did not converge.
        """
        if not self.converged:
            raise RuntimeError("Model did not converge; cannot predict.")

        t = np.asarray(times, dtype=float)
        dose = self.params.get("dose", 1.0)

        if self.model_type == "1-compartment":
            if self.route == "oral":
                return _oral_1cmt(
                    t, dose, self.params["CL_F"], self.params["Vz_F"], self.params["ka"]
                )
            return _iv_1cmt(t, dose, self.params["CL"], self.params["Vz"])
        # 2-compartment
        if self.route == "oral":
            return _oral_2cmt(
                t,
                dose,
                self.params["CL_F"],
                self.params["V1_F"],
                self.params["Q"],
                self.params["V2"],
                self.params["ka"],
            )
        raise NotImplementedError("2-compartment IV bolus fitting not yet supported.")

    def plot(self, output_path: str | Path | None = None, show: bool = False) -> None:
        """Plot observed vs fitted concentrations.

        Parameters
        ----------
        output_path : str or Path or None, optional
            Save figure to this path.
        show : bool, optional
            If True, display interactively. Default False.
        """
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(8, 5), dpi=150)

        t_obs = np.array(self.observed_times)
        c_obs = np.array(self.observed_concs)
        c_fit = np.array(self.fitted_concs)

        ax.scatter(t_obs, c_obs, color="#003366", s=50, zorder=5, label="Observed")
        ax.plot(t_obs, c_fit, "r-", linewidth=2, label="Fitted model")

        # Smooth curve
        if self.converged:
            t_smooth = np.linspace(0, float(t_obs.max()), 200)
            try:
                c_smooth = self.predict(t_smooth)
                ax.plot(t_smooth, c_smooth, "r--", alpha=0.5, linewidth=1)
            except Exception:
                pass

        ax.set_xlabel("Time")
        ax.set_ylabel("Concentration")
        title = f"{self.model_type} {self.route} fit"
        if self.converged:
            title += f" (R2={self.r_squared:.4f})"
        ax.set_title(title, fontweight="bold")
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.tight_layout()

        if output_path is not None:
            fig.savefig(output_path, bbox_inches="tight")
        if show:
            plt.show()
        plt.close(fig)


# ---------------------------------------------------------------------------
# Fitting function
# ---------------------------------------------------------------------------


def fit_pk_model(
    times: list[float] | np.ndarray,
    concs: list[float] | np.ndarray,
    *,
    dose: float,
    route: Literal["oral", "iv_bolus"] = "oral",
    model: Literal["1-compartment", "2-compartment"] = "1-compartment",
) -> PKModelFit:
    """Fit a PK model to observed concentration-time data.

    Uses scipy.optimize.curve_fit to estimate PK parameters from data.
    Returns a PKModelFit object with parameters, diagnostics, and plots.

    Parameters
    ----------
    times : list[float] or np.ndarray
        Sample times.
    concs : list[float] or np.ndarray
        Observed concentrations.
    dose : float
        Administered dose amount.
    route : {"oral", "iv_bolus"}, optional
        Route of administration. Default "oral".
    model : {"1-compartment", "2-compartment"}, optional
        Compartmental model to fit. Default "1-compartment".

    Returns
    -------
    PKModelFit
        Fit results with .summary(), .plot(), .predict() methods.

    Raises
    ------
    ValueError
        If times/concs have different lengths or insufficient data.

    Examples
    --------
    >>> result = fit_pk_model([0.5, 1, 2, 4, 8, 12],
    ...                       [2.1, 5.3, 8.1, 6.2, 3.1, 1.2],
    ...                       dose=100, route="oral")
    >>> print(result.summary())
    >>> result.plot()
    """
    t = np.asarray(times, dtype=float)
    c = np.asarray(concs, dtype=float)

    if len(t) != len(c):
        raise ValueError(f"times and concs must have the same length ({len(t)} vs {len(c)}).")
    if len(t) < 3:
        raise ValueError(f"Need at least 3 data points for fitting (got {len(t)}).")
    if np.any(c < 0):
        raise ValueError("Concentrations must be non-negative.")
    if route not in ("oral", "iv_bolus"):
        raise ValueError(f"route must be 'oral' or 'iv_bolus' (got {route!r}).")

    fit_warnings: list[str] = []

    # Suppress scipy optimize warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", OptimizeWarning)

        try:
            if model == "1-compartment":
                fit_result = _fit_1cmt(t, c, dose, route, fit_warnings)
            elif model == "2-compartment":
                fit_result = _fit_2cmt(t, c, dose, route, fit_warnings)
            else:
                raise ValueError(
                    f"model must be '1-compartment' or '2-compartment' (got {model!r})."
                )
        except Exception as exc:
            fit_warnings.append(f"Fitting failed: {exc}")
            return PKModelFit(
                model_type=model,
                route=route,
                params={},
                param_se={},
                r_squared=float("nan"),
                aic=float("nan"),
                converged=False,
                observed_times=t.tolist(),
                observed_concs=c.tolist(),
                fitted_concs=[],
                warnings=fit_warnings,
            )

    return fit_result


def _fit_1cmt(
    t: np.ndarray,
    c: np.ndarray,
    dose: float,
    route: str,
    fit_warnings: list[str],
) -> PKModelFit:
    """Fit a 1-compartment model."""
    cmax_obs = float(np.max(c))
    tmax_obs = float(t[np.argmax(c)])

    if route == "oral":
        # Initial guesses: ka ~ 1/tmax, CL_F ~ dose/AUC_est, Vz_F ~ CL_F/k
        auc_est = float(np.trapezoid(c, t)) if len(t) > 1 else 1.0
        ka_guess = max(1.0 / max(tmax_obs, 0.1), 0.1)
        cl_f_guess = max(dose / max(auc_est, 1e-6), 0.01)
        vz_f_guess = max(cl_f_guess / 0.1, 1.0)

        p0 = [cl_f_guess, vz_f_guess, ka_guess]
        bounds = ([1e-6, 1e-6, 1e-6], [np.inf, np.inf, np.inf])

        def oral_model(t_arr: np.ndarray, cl_f: float, vz_f: float, ka: float) -> np.ndarray:
            return _oral_1cmt(t_arr, dose, cl_f, vz_f, ka)

        model_fn: Callable[..., np.ndarray[Any, Any]] = oral_model
        param_names = ["CL_F", "Vz_F", "ka"]

    else:  # iv_bolus
        # Initial guesses: k ~ ln(C0/C_last)/t_last, Vz ~ dose/C0
        c0 = c[0] if t[0] == 0 else cmax_obs * 1.5
        k_guess = max(np.log(max(c0, 1e-6) / max(c[-1], 1e-6)) / max(t[-1], 1e-6), 0.01)
        vz_guess = max(dose / max(c0, 1e-6), 1.0)
        cl_guess = k_guess * vz_guess

        p0 = [cl_guess, vz_guess]
        bounds = ([1e-6, 1e-6], [np.inf, np.inf])

        def iv_model(t_arr: np.ndarray, cl: float, vz: float) -> np.ndarray:
            return _iv_1cmt(t_arr, dose, cl, vz)

        model_fn = iv_model
        param_names = ["CL", "Vz"]

    popt, pcov = curve_fit(model_fn, t, c, p0=p0, bounds=bounds, maxfev=10000)

    # Compute diagnostics
    c_pred = model_fn(t, *popt)
    ss_res = float(np.sum((c - c_pred) ** 2))
    ss_tot = float(np.sum((c - np.mean(c)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    n = len(t)
    k = len(popt)
    aic = n * np.log(max(ss_res / n, 1e-15)) + 2 * k

    # Standard errors from covariance matrix
    perr = np.sqrt(np.diag(pcov)) if pcov.size > 0 else np.full(len(popt), float("nan"))

    params = dict(zip(param_names, [float(v) for v in popt], strict=True))
    param_se = dict(zip(param_names, [float(v) for v in perr], strict=True))

    # Add dose to params for predict()
    params["dose"] = dose

    return PKModelFit(
        model_type="1-compartment",
        route=route,
        params=params,
        param_se=param_se,
        r_squared=r2,
        aic=float(aic),
        converged=True,
        observed_times=t.tolist(),
        observed_concs=c.tolist(),
        fitted_concs=c_pred.tolist(),
        warnings=fit_warnings,
    )


def _fit_2cmt(
    t: np.ndarray,
    c: np.ndarray,
    dose: float,
    route: str,
    fit_warnings: list[str],
) -> PKModelFit:
    """Fit a 2-compartment model."""
    tmax_obs = float(t[np.argmax(c)])

    if route == "oral":
        auc_est = float(np.trapezoid(c, t)) if len(t) > 1 else 1.0
        ka_guess = max(1.0 / max(tmax_obs, 0.1), 0.1)
        cl_f_guess = max(dose / max(auc_est, 1e-6), 0.01)
        v1_f_guess = max(cl_f_guess / 0.5, 1.0)
        q_guess = max(cl_f_guess * 0.3, 0.1)
        v2_guess = max(v1_f_guess * 0.5, 1.0)

        p0 = [cl_f_guess, v1_f_guess, q_guess, v2_guess, ka_guess]
        bounds = ([1e-6, 1e-6, 1e-6, 1e-6, 1e-6], [np.inf, np.inf, np.inf, np.inf, np.inf])

        def model_fn(
            t_arr: np.ndarray, cl_f: float, v1_f: float, q: float, v2: float, ka: float
        ) -> np.ndarray:
            return _oral_2cmt(t_arr, dose, cl_f, v1_f, q, v2, ka)

        param_names = ["CL_F", "V1_F", "Q", "V2", "ka"]

    else:
        raise NotImplementedError(
            "2-compartment IV bolus fitting is not yet supported. "
            "Use route='oral' or model='1-compartment'."
        )

    popt, pcov = curve_fit(model_fn, t, c, p0=p0, bounds=bounds, maxfev=10000)

    c_pred = model_fn(t, *popt)
    ss_res = float(np.sum((c - c_pred) ** 2))
    ss_tot = float(np.sum((c - np.mean(c)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    n = len(t)
    k = len(popt)
    aic = n * np.log(max(ss_res / n, 1e-15)) + 2 * k

    perr = np.sqrt(np.diag(pcov)) if pcov.size > 0 else np.full(len(popt), float("nan"))

    params = dict(zip(param_names, [float(v) for v in popt], strict=True))
    param_se = dict(zip(param_names, [float(v) for v in perr], strict=True))
    params["dose"] = dose

    # Compute alpha/beta for half-life
    k10 = params["CL_F"] / params["V1_F"]
    k12 = params["Q"] / params["V1_F"]
    k21 = params["Q"] / params["V2"]
    a = k12 + k21 + k10
    b = k10 * k21
    disc = max(a * a - 4 * b, 0.0)
    sqrt_disc = math.sqrt(disc)
    params["alpha"] = (a + sqrt_disc) / 2.0
    params["beta"] = (a - sqrt_disc) / 2.0

    return PKModelFit(
        model_type="2-compartment",
        route=route,
        params=params,
        param_se=param_se,
        r_squared=r2,
        aic=float(aic),
        converged=True,
        observed_times=t.tolist(),
        observed_concs=c.tolist(),
        fitted_concs=c_pred.tolist(),
        warnings=fit_warnings,
    )
