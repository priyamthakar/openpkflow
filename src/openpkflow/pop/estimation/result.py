"""PopPKResult dataclass — population PK estimation output."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class PopPKResult:
    """Result of population PK estimation (FOCE-I or SAEM).

    Parameters
    ----------
    method : str
        ``"FOCE-I"`` or ``"SAEM"``.
    route : str
        ``"oral"`` or ``"iv_bolus"``.
    converged : bool
        Whether the estimation converged.
    uncertainty_reliable : bool
        Whether Fisher information matrix was positive-definite.
    n_subjects : int
        Number of subjects.
    n_observations : int
        Total number of observations.
    minus2ll : float
        Final -2 log-likelihood.
    aic : float
        Akaike Information Criterion.
    bic : float
        Bayesian Information Criterion.
    theta_pop : dict[str, float]
        Population typical values on natural scale.
    theta_se : dict[str, float]
        Standard errors of theta_pop.
    omega_diag : dict[str, float]
        Estimated Omega diagonal elements (log-scale variances).
    omega_se : dict[str, float]
        Standard errors of omega_diag.
    sigma_prop : float
        Estimated proportional error.
    sigma_add : float
        Estimated additive error.
    sigma_prop_se : float
        Standard error of sigma_prop.
    sigma_add_se : float
        Standard error of sigma_add.
    shrinkage : dict[str, float]
        EBE shrinkage per parameter (0-1).
    ebe : pd.DataFrame
        Empirical Bayes Estimates per subject (columns: ID, eta_...).
    individual_predictions : dict[str, np.ndarray]
        IPRED per subject keyed by subject ID.
    population_predictions : np.ndarray
        PRED for all observations.
    gradient_norm : float
        Gradient norm at solution.
    condition_number : float
        Fisher information condition number.
    n_inner_failures : int
        Number of subjects with failed EBE optimization.
    iterations : int
        Number of outer iterations or SAEM cycles.
    elapsed_time : float
        Wall-clock time in seconds.
    warnings : list[str]
        Diagnostic warnings.
    study_label : str
        Optional label for reports.
    """

    method: str
    route: str
    converged: bool
    uncertainty_reliable: bool
    n_subjects: int
    n_observations: int
    minus2ll: float
    aic: float
    bic: float
    theta_pop: dict[str, float]
    theta_se: dict[str, float]
    omega_diag: dict[str, float]
    omega_se: dict[str, float]
    sigma_prop: float
    sigma_add: float
    sigma_prop_se: float
    sigma_add_se: float
    shrinkage: dict[str, float]
    ebe: pd.DataFrame
    individual_predictions: dict[str, np.ndarray]
    population_predictions: np.ndarray
    observed_times: dict[str, np.ndarray]
    observed_concentrations: dict[str, np.ndarray]
    gradient_norm: float
    condition_number: float
    n_inner_failures: int
    iterations: int
    elapsed_time: float
    warnings: list[str] = field(default_factory=list)
    study_label: str = ""

    @property
    def param_names(self) -> list[str]:
        """Ordered parameter names."""
        return list(self.theta_pop.keys())

    @property
    def n_params(self) -> int:
        """Number of fixed-effect parameters."""
        return len(self.theta_pop)

    @property
    def rse(self) -> dict[str, float]:
        """Relative standard errors (%) per parameter."""
        result: dict[str, float] = {}
        for k in self.param_names:
            if self.theta_pop[k] != 0 and k in self.theta_se:
                result[k] = 100.0 * self.theta_se[k] / self.theta_pop[k]
            else:
                result[k] = float("nan")
        return result

    def summary(self) -> str:
        """Return an ASCII multi-line summary of the estimation results.

        Returns
        -------
        str
            Formatted summary string.
        """
        lines: list[str] = []
        lines.append(f"Population PK Estimation -- {self.method}")
        lines.append(f"Study: {self.study_label}" if self.study_label else "")
        lines.append(f"Route: {self.route}")
        lines.append(f"Subjects: {self.n_subjects}  Observations: {self.n_observations}")
        lines.append("")

        lines.append("Fixed Effects (Population Typical Values)")
        lines.append("-" * 55)
        lines.append(f"{'Parameter':<12} {'Estimate':>12} {'SE':>12} {'RSE%':>12}")
        lines.append("-" * 55)
        for k in self.param_names:
            est = self.theta_pop.get(k, float("nan"))
            se = self.theta_se.get(k, float("nan"))
            rse_val = self.rse.get(k, float("nan"))
            lines.append(f"{k:<12} {est:12.4f} {se:12.4f} {rse_val:11.1f}")
        lines.append("")

        lines.append("Between-Subject Variability (Omega diagonal)")
        lines.append("-" * 55)
        lines.append(f"{'Parameter':<12} {'Omega':>12} {'SE':>12} {'RSE%':>12}")
        lines.append("-" * 55)
        for k in self.param_names:
            omega_val = self.omega_diag.get(k, float("nan"))
            omega_se_val = self.omega_se.get(k, float("nan"))
            omega_rse = (
                100.0 * omega_se_val / omega_val
                if omega_val > 0 and omega_se_val > 0
                else float("nan")
            )
            lines.append(
                f"{'omega_' + k:<12} {omega_val:12.4f} {omega_se_val:12.4f} {omega_rse:11.1f}"
            )
        lines.append("")

        lines.append("Residual Error")
        lines.append("-" * 40)
        lines.append(f"  sigma_prop = {self.sigma_prop:.4f}  (SE = {self.sigma_prop_se:.4f})")
        lines.append(f"  sigma_add  = {self.sigma_add:.4f}   (SE = {self.sigma_add_se:.4f})")
        lines.append("")

        lines.append("EBE Shrinkage")
        lines.append("-" * 40)
        for k, v in self.shrinkage.items():
            lines.append(f"  {k}: {v:.1%}")
        lines.append("")

        lines.append("Model Fit")
        lines.append("-" * 40)
        lines.append(f"  -2LL = {self.minus2ll:.1f}")
        lines.append(f"  AIC  = {self.aic:.1f}")
        lines.append(f"  BIC  = {self.bic:.1f}")
        lines.append(f"  Converged: {self.converged}")
        lines.append(f"  Uncertainty reliable: {self.uncertainty_reliable}")
        lines.append(f"  Gradient norm: {self.gradient_norm:.2e}")
        lines.append(
            f"  Condition number: {self.condition_number:.1f}"
            if np.isfinite(self.condition_number)
            else ""
        )
        lines.append(f"  EBE failures: {self.n_inner_failures}/{self.n_subjects}")
        lines.append(f"  Iterations: {self.iterations}")
        lines.append(f"  Elapsed time: {self.elapsed_time:.1f}s")
        lines.append("")

        if self.warnings:
            lines.append("Warnings")
            lines.append("-" * 40)
            for w in self.warnings:
                lines.append(f"  * {w}")
            lines.append("")

        lines.append("Disclaimer: This is a research tool. Results should be verified")
        lines.append("against a regulatory-grade population PK engine (NONMEM, Monolix).")

        return "\n".join(lines)

    def to_dataframe(self) -> pd.DataFrame:
        """Return a DataFrame of population parameter estimates.

        Returns
        -------
        pd.DataFrame
            Table with rows for each parameter type.
        """
        rows: list[dict[str, object]] = []
        for k in self.param_names:
            rows.append(
                {
                    "type": "theta",
                    "parameter": k,
                    "estimate": self.theta_pop.get(k),
                    "se": self.theta_se.get(k),
                    "rse_pct": self.rse.get(k),
                }
            )
        for k in self.param_names:
            rows.append(
                {
                    "type": "omega",
                    "parameter": f"omega_{k}",
                    "estimate": self.omega_diag.get(k),
                    "se": self.omega_se.get(k),
                    "rse_pct": (
                        100.0 * self.omega_se.get(k, 0) / self.omega_diag.get(k, 1)
                        if self.omega_diag.get(k, 0) > 0
                        else float("nan")
                    ),
                }
            )
        rows.append(
            {
                "type": "sigma",
                "parameter": "sigma_prop",
                "estimate": self.sigma_prop,
                "se": self.sigma_prop_se,
                "rse_pct": float("nan"),
            }
        )
        rows.append(
            {
                "type": "sigma",
                "parameter": "sigma_add",
                "estimate": self.sigma_add,
                "se": self.sigma_add_se,
                "rse_pct": float("nan"),
            }
        )
        return pd.DataFrame(rows)

    def to_dict(self) -> dict[str, object]:
        """Return a dictionary of scalar results (no raw EBE or predictions).

        Returns
        -------
        dict
            Scalar estimation results.
        """
        return {
            "method": self.method,
            "route": self.route,
            "converged": self.converged,
            "uncertainty_reliable": self.uncertainty_reliable,
            "n_subjects": self.n_subjects,
            "n_observations": self.n_observations,
            "minus2ll": self.minus2ll,
            "aic": self.aic,
            "bic": self.bic,
            "theta_pop": self.theta_pop,
            "theta_se": self.theta_se,
            "omega_diag": self.omega_diag,
            "omega_se": self.omega_se,
            "sigma_prop": self.sigma_prop,
            "sigma_add": self.sigma_add,
            "sigma_prop_se": self.sigma_prop_se,
            "sigma_add_se": self.sigma_add_se,
            "shrinkage": self.shrinkage,
            "gradient_norm": self.gradient_norm,
            "condition_number": self.condition_number,
            "n_inner_failures": self.n_inner_failures,
            "iterations": self.iterations,
            "elapsed_time": self.elapsed_time,
            "warnings": self.warnings,
            "study_label": self.study_label,
        }

    def plot(
        self,
        output_path: str | None = None,
        show: bool = False,
    ) -> None:
        """Generate a 6-panel population PK diagnostic plot.

        Parameters
        ----------
        output_path : str | None
            If provided, save to this path.
        show : bool
            If True, display the plot.
        """
        import matplotlib.pyplot as plt

        from .plotting import pop_pk_figure

        fig = pop_pk_figure(self)
        if output_path:
            fig.savefig(output_path, dpi=150, bbox_inches="tight")
        if show:
            plt.show()
        else:
            plt.close(fig)

    def report(
        self,
        output_path: str,
        *,
        fmt: str = "html",
    ) -> str | bytes:
        """Generate a population PK estimation report.

        Parameters
        ----------
        output_path : str
            Path for the output file.
        fmt : str
            ``"html"`` or ``"markdown"``.

        Returns
        -------
        str or bytes
            Report content.
        """
        from .reporting import report_pop_pk

        return report_pop_pk(self, output_path=output_path, fmt=fmt)
