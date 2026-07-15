"""PopPKResult dataclass — population PK estimation output."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class PopPKResult:
    """Result of population PK estimation (FOCE-I or SAEM)."""

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
    omega_off_diag: dict[str, float] = field(default_factory=dict)
    omega_off_se: dict[str, float] = field(default_factory=dict)
    sigma_prop: float = 0.15
    sigma_add: float = 0.0
    sigma_prop_se: float = float("nan")
    sigma_add_se: float = float("nan")
    shrinkage: dict[str, float] = field(default_factory=dict)
    ebe: pd.DataFrame = field(default_factory=pd.DataFrame)
    individual_predictions: dict[str, np.ndarray] = field(default_factory=dict)
    population_predictions: np.ndarray = field(default_factory=lambda: np.array([]))
    observed_times: dict[str, np.ndarray] = field(default_factory=dict)
    observed_concentrations: dict[str, np.ndarray] = field(default_factory=dict)
    gradient_norm: float = 0.0
    condition_number: float = float("nan")
    n_inner_failures: int = 0
    iterations: int = 0
    elapsed_time: float = 0.0
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
        """Return an ASCII multi-line summary of the estimation results."""
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

        if self.omega_off_diag:
            lines.append("Between-Subject Variability (Omega matrix)")
        else:
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
        if self.omega_off_diag:
            for k, v in self.omega_off_diag.items():
                se_val = self.omega_off_se.get(k, float("nan"))
                lines.append(f"  cov({k}): {v:.4f} (SE: {se_val:.4f})")
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
        if np.isfinite(self.condition_number):
            lines.append(f"  Condition number: {self.condition_number:.1f}")
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
        """Return a DataFrame of population parameter estimates."""
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
        for k, v in self.omega_off_diag.items():
            rows.append(
                {
                    "type": "omega_cov",
                    "parameter": f"cov({k})",
                    "estimate": v,
                    "se": self.omega_off_se.get(k, float("nan")),
                    "rse_pct": float("nan"),
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
        """Return a dictionary of scalar results."""
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
            "omega_off_diag": self.omega_off_diag,
            "omega_off_se": self.omega_off_se,
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

    def plot(self, output_path: str | Path | None = None, show: bool = False) -> None:
        """Generate a 6-panel population PK diagnostic plot."""
        import matplotlib.pyplot as plt

        from .plotting import pop_pk_figure

        fig = pop_pk_figure(self)
        if output_path:
            fig.savefig(output_path, dpi=150, bbox_inches="tight")
        if show:
            plt.show()
        else:
            plt.close(fig)

    def report(self, output_path: str | Path, *, fmt: str = "html") -> str:
        """Generate a population PK estimation report."""
        from .reporting import report_pop_pk

        return report_pop_pk(self, output_path=output_path, fmt=fmt)
