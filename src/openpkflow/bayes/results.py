"""MapPKResult dataclass for MAP individual PK estimation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from .priors import PKPrior


@dataclass
class MapPKResult:
    """Result of MAP individual PK estimation.

    Attributes
    ----------
    subject : str
        Subject identifier.
    route : str
        Route of administration ("oral" or "iv_bolus").
    dose : float
        Administered dose.
    n_observations : int
        Number of observed concentrations used.
    converged : bool
        Whether the optimizer converged successfully.
    uncertainty_reliable : bool
        Whether the Hessian was positive-definite and SEs are trustworthy.
    CL_F : float or None
        Apparent oral clearance (oral route).
    Vz_F : float or None
        Apparent volume of distribution (oral route).
    ka : float or None
        Absorption rate constant (oral route).
    CL : float or None
        Systemic clearance (iv_bolus route).
    Vz : float or None
        Volume of distribution (iv_bolus route).
    CL_F_se : float or None
        Standard error of CL_F (delta-method, natural scale).
    Vz_F_se : float or None
        Standard error of Vz_F.
    ka_se : float or None
        Standard error of ka.
    CL_se : float or None
        Standard error of CL.
    Vz_se : float or None
        Standard error of Vz.
    k : float
        Elimination rate constant (1/h).
    half_life : float
        Terminal half-life (h).
    AUCinf : float
        AUC to infinity = dose / CL (or dose / CL_F).
    Cmax : float
        Predicted Cmax from model.
    Tmax : float
        Predicted Tmax from model.
    gradient_norm : float
        Gradient norm at solution; < 1e-3 indicates good convergence.
    condition_number : float
        Hessian condition number; > 1e6 indicates near-singular Hessian.
    objective_value : float
        Negative log-posterior at MAP solution (>= 0).
    prior : PKPrior
        Prior used for this estimation.
    time_points : list[float]
        Observed sampling times.
    observed_conc : list[float]
        Observed concentrations.
    predicted_conc : list[float]
        Model-predicted concentrations at observed times.
    warnings : list[str]
        Diagnostic warnings raised during estimation.
    """

    subject: str
    route: str
    dose: float
    n_observations: int
    converged: bool
    uncertainty_reliable: bool
    CL_F: float | None
    Vz_F: float | None
    ka: float | None
    CL: float | None
    Vz: float | None
    CL_F_se: float | None
    Vz_F_se: float | None
    ka_se: float | None
    CL_se: float | None
    Vz_se: float | None
    k: float
    half_life: float
    AUCinf: float
    Cmax: float
    Tmax: float
    gradient_norm: float
    condition_number: float
    objective_value: float
    prior: PKPrior
    time_points: list[float] = field(default_factory=list)
    observed_conc: list[float] = field(default_factory=list)
    predicted_conc: list[float] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def summary(self) -> str:
        """Return a plain-text summary of the MAP estimation result.

        Returns
        -------
        str
            Multi-line ASCII summary including parameters, diagnostics, and disclaimer.
        """
        title = f"MAP Individual PK{' -- ' + self.subject if self.subject else ''}"
        lines = [
            title,
            "=" * len(title),
            f"Route: {self.route} | Dose: {self.dose:.4g} | Observations: {self.n_observations}",
            f"Converged: {'Yes' if self.converged else 'No'} | "
            f"Uncertainty reliable: {'Yes' if self.uncertainty_reliable else 'No'}",
            f"Gradient norm: {self.gradient_norm:.3e} | "
            f"Hessian condition: {self.condition_number:.2e}",
            "",
        ]

        if self.route == "oral":
            cl_str = f"  CL_F = {self.CL_F:.4g} L/h"
            if self.CL_F_se is not None:
                cl_str += f"  (SE {self.CL_F_se:.4g})"
            v_str = f"  Vz_F = {self.Vz_F:.4g} L"
            if self.Vz_F_se is not None:
                v_str += f"  (SE {self.Vz_F_se:.4g})"
            ka_str = f"  ka   = {self.ka:.4g} 1/h"
            if self.ka_se is not None:
                ka_str += f"  (SE {self.ka_se:.4g})"
            lines += ["MAP Parameters (1-cmt oral):", cl_str, v_str, ka_str]
        else:
            cl_str = f"  CL   = {self.CL:.4g} L/h"
            if self.CL_se is not None:
                cl_str += f"  (SE {self.CL_se:.4g})"
            v_str = f"  Vz   = {self.Vz:.4g} L"
            if self.Vz_se is not None:
                v_str += f"  (SE {self.Vz_se:.4g})"
            lines += ["MAP Parameters (1-cmt IV bolus):", cl_str, v_str]

        lines += [
            f"  k    = {self.k:.4g} 1/h",
            f"  t1/2 = {self.half_life:.4g} h",
            "",
            "Derived PK Parameters:",
            f"  AUCinf = {self.AUCinf:.4g} h*conc",
            f"  Cmax   = {self.Cmax:.4g} conc",
            f"  Tmax   = {self.Tmax:.4g} h",
        ]

        if self.warnings:
            lines += ["", "Warnings:"] + [f"  [!] {w}" for w in self.warnings]

        lines += [
            "",
            "Disclaimer: This report was generated using OpenPKFlow (open-source).",
            "Final regulatory interpretation should be reviewed by qualified experts.",
        ]
        return "\n".join(lines)

    def to_dict(self) -> dict[str, object]:
        """Return a plain-dict representation of the result.

        Returns
        -------
        dict[str, object]
            All fields serialized to basic Python types.
        """
        return {
            "subject": self.subject,
            "route": self.route,
            "dose": self.dose,
            "n_observations": self.n_observations,
            "converged": self.converged,
            "uncertainty_reliable": self.uncertainty_reliable,
            "CL_F": self.CL_F,
            "Vz_F": self.Vz_F,
            "ka": self.ka,
            "CL": self.CL,
            "Vz": self.Vz,
            "CL_F_se": self.CL_F_se,
            "Vz_F_se": self.Vz_F_se,
            "ka_se": self.ka_se,
            "CL_se": self.CL_se,
            "Vz_se": self.Vz_se,
            "k": self.k,
            "half_life": self.half_life,
            "AUCinf": self.AUCinf,
            "Cmax": self.Cmax,
            "Tmax": self.Tmax,
            "gradient_norm": self.gradient_norm,
            "condition_number": self.condition_number,
            "objective_value": self.objective_value,
            "warnings": self.warnings,
            "time_points": self.time_points,
            "observed_conc": self.observed_conc,
            "predicted_conc": self.predicted_conc,
        }

    def plot(
        self,
        output_path: str | Path | None = None,
        show: bool = False,
    ) -> None:
        """Plot observed concentrations against MAP-predicted profile.

        Parameters
        ----------
        output_path : str or Path or None, optional
            If provided, saves the figure to this path.
        show : bool, optional
            If True, calls plt.show(). Default False.
        """
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        t = np.array(self.time_points)
        t_dense = np.linspace(0, t[-1] * 1.5, 500) if len(t) > 0 else np.array([])

        from openpkflow.sim.methods import c_1cmt_iv_bolus, c_1cmt_oral

        if len(t_dense) > 0:
            if self.route == "oral" and self.CL_F and self.Vz_F and self.ka:
                c_model = c_1cmt_oral(t_dense, self.dose, self.CL_F, self.Vz_F, self.ka)
            elif self.route == "iv_bolus" and self.CL and self.Vz:
                c_model = c_1cmt_iv_bolus(t_dense, self.dose, self.CL, self.Vz)
            else:
                c_model = None
        else:
            c_model = None

        fig, ax = plt.subplots(figsize=(6, 4), dpi=150)
        if c_model is not None:
            status = "MAP" if self.converged else "MAP (not converged)"
            ax.plot(t_dense, c_model, "-", color="#0d3b66", linewidth=1.5, label=status)
        ax.scatter(
            self.time_points,
            self.observed_conc,
            color="#cc3300",
            s=40,
            zorder=5,
            label=f"Observed (n={self.n_observations})",
        )
        title = f"MAP Individual PK{' -- ' + self.subject if self.subject else ''}"
        ax.set_title(title, fontsize=11)
        ax.set_xlabel("Time (h)", fontsize=10)
        ax.set_ylabel("Concentration", fontsize=10)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
        fig.tight_layout()

        if output_path is not None:
            fig.savefig(output_path, bbox_inches="tight")
        if show:
            plt.show()
        plt.close(fig)

    def report(
        self,
        output_path: str | Path,
        format: str = "html",
    ) -> str | bytes:
        """Generate a report for this MAP result.

        Parameters
        ----------
        output_path : str or Path
            Where to save the report file.
        format : str, optional
            "html", "markdown", "pdf", or "docx". Defaults to "html".

        Returns
        -------
        str | bytes
            Rendered report content.
        """
        from .reporting import report_map_pk

        return report_map_pk(self, output_path=output_path, format=format)
