"""Sparse-sampling NCA: model-informed PK parameters from limited data."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import curve_fit

from openpkflow.sim.methods import c_1cmt_oral


def fit_sparse_1cmt_oral(
    times: list[float] | np.ndarray,
    concentrations: list[float] | np.ndarray,
    dose: float,
    *,
    p0: tuple[float, float, float] | None = None,
    bounds: tuple[tuple[float, float, float], tuple[float, float, float]] | None = None,
) -> SparseNCAResult:
    r"""Fit a 1-compartment oral model to sparse PK data.

    Uses scipy ``curve_fit`` to estimate apparent clearance (CL_F),
    apparent volume (Vz_F), and absorption rate constant (ka)
    from as few as 3 data points. Computes model-derived NCA
    parameters: AUClast, AUCinf, Cmax, Tmax, half-life.

    Parameters
    ----------
    times :
        Sampling times (h), must have >= 3 points.
    concentrations :
        Observed concentrations at each time.
    dose :
        Dose amount (mg).
    p0 :
        Initial guess for (CL_F, Vz_F, ka). Defaults to
        dose-based heuristics.
    bounds :
        (lower, upper) bounds for each parameter. Defaults to
        (0.01, 0.1, 0.01) -> (1000, 10000, 10).

    Returns
    -------
    SparseNCAResult
        Model-fitted PK parameters.

    References
    ----------
    Rowland & Tozer, Clinical Pharmacokinetics (2011), Ch. 3 & 5.
    """
    t = np.asarray(times, dtype=float)
    c = np.asarray(concentrations, dtype=float)

    if len(t) < 3:
        raise ValueError("Sparse NCA requires at least 3 time-concentration pairs.")
    if len(t) != len(c):
        raise ValueError("times and concentrations must have the same length.")
    if dose <= 0:
        raise ValueError("dose must be > 0.")

    # Heuristic initial guesses
    if p0 is None:
        cl0 = dose / (np.trapezoid(c, t) + 1e-9)
        vz0 = dose / np.max(c) if np.max(c) > 0 else 10.0
        ka0 = 1.0
        p0 = (cl0, vz0, ka0)

    if bounds is None:
        bounds = ((0.01, 0.1, 0.01), (1000.0, 10000.0, 10.0))

    def _model(t_eval: np.ndarray, CL_F: float, Vz_F: float, ka: float) -> np.ndarray:
        return c_1cmt_oral(t_eval, dose, CL_F, Vz_F, ka)

    try:
        popt, pcov = curve_fit(_model, t, c, p0=p0, bounds=bounds, maxfev=20_000, ftol=1e-8)
        converged = True
        CL_F, Vz_F, ka = popt[0], popt[1], popt[2]
    except (RuntimeError, ValueError):
        converged = False
        CL_F, Vz_F, ka = p0[0], p0[1], p0[2]
        pcov = None

    # Derived parameters
    if converged and pcov is not None:
        perr = np.sqrt(np.diag(pcov))
        cl_se, vz_se, ka_se = perr[0], perr[1], perr[2]
    else:
        cl_se = vz_se = ka_se = None

    k = CL_F / Vz_F
    half_life = np.log(2.0) / k if k > 0 else float("nan")
    AUCinf = dose / CL_F if CL_F > 0 else float("nan")

    # Model-predicted concentrations at observed times
    pred = _model(t, CL_F, Vz_F, ka)
    fitted_conc = pred.tolist()

    # AUClast from trapezoidal integration of predicted profile
    AUClast = float(np.trapezoid(pred[0 : len(t)], t[0 : len(t)]))

    # Cmax and Tmax from model-predicted profile (dense grid)
    t_dense = np.linspace(0, t[-1] * 1.5, 500)
    c_dense = _model(t_dense, CL_F, Vz_F, ka)
    idx_max = int(np.argmax(c_dense))
    Cmax = float(c_dense[idx_max])
    Tmax = float(t_dense[idx_max])

    return SparseNCAResult(
        subject="",
        dose=dose,
        route="oral",
        n_samples=len(t),
        converged=converged,
        CL_F=float(CL_F),
        Vz_F=float(Vz_F),
        ka=float(ka),
        k=float(k),
        half_life=float(half_life),
        CL_F_se=float(cl_se) if cl_se is not None else None,
        Vz_F_se=float(vz_se) if vz_se is not None else None,
        ka_se=float(ka_se) if ka_se is not None else None,
        AUClast=AUClast,
        AUCinf=AUCinf,
        Cmax=Cmax,
        Tmax=Tmax,
        time_points=t.tolist(),
        observed_conc=c.tolist(),
        fitted_conc=fitted_conc,
    )


@dataclass
class SparseNCAResult:
    """Model-informed NCA result from sparse-sampling data.

    Attributes
    ----------
    subject : str
        Subject identifier.
    dose : float
        Administered dose (mg).
    route : str
        Route of administration.
    n_samples : int
        Number of observed samples used in the fit.
    converged : bool
        Whether the curve fit converged successfully.
    CL_F : float
        Fitted apparent oral clearance (L/h).
    Vz_F : float
        Fitted apparent volume of distribution (L).
    ka : float
        Fitted absorption rate constant (1/h).
    k : float
        Elimination rate constant = CL_F / Vz_F (1/h).
    half_life : float
        Terminal half-life (h).
    CL_F_se : float or None
        Standard error of CL_F estimate.
    Vz_F_se : float or None
        Standard error of Vz_F estimate.
    ka_se : float or None
        Standard error of ka estimate.
    AUClast : float
        AUC to last observed time from model profile (h * ng/mL).
    AUCinf : float
        AUC to infinity = dose / CL_F (h * ng/mL).
    Cmax : float
        Maximum predicted concentration (ng/mL).
    Tmax : float
        Time of maximum predicted concentration (h).
    time_points : list[float]
        Observed sampling times.
    observed_conc : list[float]
        Observed concentrations at each time.
    fitted_conc : list[float]
        Model-predicted concentrations at observed times.
    """

    subject: str
    dose: float
    route: str
    n_samples: int
    converged: bool
    CL_F: float
    Vz_F: float
    ka: float
    k: float
    half_life: float
    CL_F_se: float | None = None
    Vz_F_se: float | None = None
    ka_se: float | None = None
    AUClast: float = float("nan")
    AUCinf: float = float("nan")
    Cmax: float = float("nan")
    Tmax: float = float("nan")
    time_points: list[float] | None = None
    observed_conc: list[float] | None = None
    fitted_conc: list[float] | None = None

    def summary(self) -> str:
        lines = [
            f"Sparse NCA Results{f' — Subject {self.subject}' if self.subject else ''}",
            f"{'=' * 50}",
            f"Route: {self.route} | Dose: {self.dose:.4g} mg | Samples: {self.n_samples}",
            f"Converged: {'Yes' if self.converged else 'No'}",
            "",
            "Fitted Parameters (1-cmt oral):",
            f"  CL_F  = {self.CL_F:.4g} L/h",
            f"  Vz_F  = {self.Vz_F:.4g} L",
            f"  ka    = {self.ka:.4g} 1/h",
            f"  k     = {self.k:.4g} 1/h",
            f"  t1/2  = {self.half_life:.4g} h",
        ]
        if self.CL_F_se is not None:
            lines.append("")
            lines.append("Standard Errors:")
            lines.append(f"  CL_F  = {self.CL_F_se:.4g} L/h")
            lines.append(f"  Vz_F  = {self.Vz_F_se:.4g} L")
            lines.append(f"  ka    = {self.ka_se:.4g} 1/h")
        lines.append("")
        lines.append("Derived Parameters:")
        lines.append(f"  AUClast  = {self.AUClast:.4g} h*ng/mL")
        lines.append(f"  AUCinf   = {self.AUCinf:.4g} h*ng/mL")
        lines.append(f"  Cmax     = {self.Cmax:.4g} ng/mL")
        lines.append(f"  Tmax     = {self.Tmax:.4g} h")

        if self.time_points and self.observed_conc:
            lines.append("")
            lines.append("Observed vs Fitted:")
            lines.append(f"{'Time':>8} {'Obs':>12} {'Fit':>12} {'Resid':>12}")
            for t, obs, fit in zip(
                self.time_points, self.observed_conc, self.fitted_conc or [], strict=False
            ):
                lines.append(f"{t:>8.2f} {obs:>12.4g} {fit:>12.4g} {obs - fit:>12.4g}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, object]:
        return {
            "subject": self.subject,
            "dose": self.dose,
            "route": self.route,
            "n_samples": self.n_samples,
            "converged": self.converged,
            "CL_F": self.CL_F,
            "Vz_F": self.Vz_F,
            "ka": self.ka,
            "k": self.k,
            "half_life": self.half_life,
            "CL_F_se": self.CL_F_se,
            "Vz_F_se": self.Vz_F_se,
            "ka_se": self.ka_se,
            "AUClast": self.AUClast,
            "AUCinf": self.AUCinf,
            "Cmax": self.Cmax,
            "Tmax": self.Tmax,
            "time_points": self.time_points,
            "observed_conc": self.observed_conc,
            "fitted_conc": self.fitted_conc,
        }

    def plot(self, output_path: str | None = None, show: bool = False) -> None:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(6, 4))
        if self.time_points is not None and self.observed_conc is not None:
            t_dense = np.linspace(0, max(self.time_points) * 1.3, 300)
            from openpkflow.sim.methods import c_1cmt_oral

            c_pred = c_1cmt_oral(t_dense, self.dose, self.CL_F, self.Vz_F, self.ka)
            ax.plot(t_dense, c_pred, "-", color="#0d3b66", linewidth=1.5, label="Fitted model")
            ax.scatter(
                self.time_points,
                self.observed_conc,
                color="#cc3300",
                s=40,
                zorder=5,
                label=f"Observed (n={self.n_samples})",
            )
        ax.set_xlabel("Time (h)")
        ax.set_ylabel("Concentration (ng/mL)")
        title = f"Sparse NCA — {self.subject}" if self.subject else "Sparse NCA Fit"
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.tight_layout()

        if output_path:
            fig.savefig(output_path, dpi=300, bbox_inches="tight")
        if show:
            plt.show()
        if not output_path and not show:
            plt.close(fig)


def sparse_nca_bias_analysis(
    sparse_result: SparseNCAResult,
    rich_result: object,
) -> dict[str, object]:
    """Compare sparse-NCA parameters against rich-sampling reference.

    Parameters
    ----------
    sparse_result : SparseNCAResult
        Sparse-sampling NCA result.
    rich_result : object
        Reference result with attributes AUClast, AUCinf_obs, Cmax, Tmax,
        half_life, CL_F, Vz_F. Typically an NCAResult from the full profile.

    Returns
    -------
    dict
        Dictionary with pct_bias for each parameter.
    """

    def _pct_bias(sparse_val: float, rich_val: float | None) -> float | None:
        if rich_val is None or rich_val == 0:
            return None
        return 100.0 * (sparse_val - rich_val) / rich_val

    return {
        "biased_parameters": {
            "AUClast_pct_bias": _pct_bias(
                sparse_result.AUClast, getattr(rich_result, "AUClast", None)
            ),
            "AUCinf_pct_bias": _pct_bias(
                sparse_result.AUCinf, getattr(rich_result, "AUCinf_obs", None)
            ),
            "Cmax_pct_bias": _pct_bias(sparse_result.Cmax, getattr(rich_result, "Cmax", None)),
            "Tmax_pct_bias": _pct_bias(sparse_result.Tmax, getattr(rich_result, "Tmax", None)),
            "half_life_pct_bias": _pct_bias(
                sparse_result.half_life, getattr(rich_result, "half_life", None)
            ),
            "CL_F_pct_bias": _pct_bias(sparse_result.CL_F, getattr(rich_result, "CL_F", None)),
            "Vz_F_pct_bias": _pct_bias(sparse_result.Vz_F, getattr(rich_result, "Vz_F", None)),
        }
    }
