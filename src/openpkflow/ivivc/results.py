"""IVIVC result types."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

_DISCLAIMER = (
    "This report was generated using OpenPKFlow -- an open-source Python workflow "
    "for pharmacometric analysis. Final regulatory interpretation should be reviewed "
    "by qualified formulation, pharmacokinetic, and regulatory experts."
)


@dataclass
class IVIVCResult:
    """Result of an IVIVC Level A analysis.

    Parameters
    ----------
    method : str
        Deconvolution method used: ``"wagner_nelson"`` or ``"loo_riegelman"``.
    times : np.ndarray
        In vivo plasma sampling times.
    concentrations : np.ndarray
        Observed plasma concentrations.
    fa : np.ndarray
        Cumulative fraction absorbed at each in vivo time point.
    levy_plot : dict[str, np.ndarray]
        Levy plot data from ``levy_plot_data()``.
    ivt_times : np.ndarray
        In vitro dissolution time points.
    ivt_fraction : np.ndarray
        Cumulative fraction dissolved.
    predicted_times : np.ndarray
        Convolution-predicted plasma time points.
    predicted_concs : np.ndarray
        Convolution-predicted concentrations.
    predictability : dict[str, float]
        Predictability assessment results.
    study_label : str, optional
        Optional label for this IVIVC study.
    """

    method: str
    times: np.ndarray
    concentrations: np.ndarray
    fa: np.ndarray
    levy_plot: dict[str, Any]
    ivt_times: np.ndarray
    ivt_fraction: np.ndarray
    predicted_times: np.ndarray
    predicted_concs: np.ndarray
    predictability: dict[str, Any]
    study_label: str = ""

    # Internal state for interpolation
    _fa_interpolator: Any = field(default=None, repr=False)

    def summary(self) -> str:
        """Return a human-readable text summary.

        Returns
        -------
        str
            Multi-line summary with deconvolution, Levy plot, and
            predictability results.
        """
        lp = self.levy_plot
        pp = self.predictability

        overall_raw = pp.get("overall_pass")
        if overall_raw is None:
            overall = "N/A (single-formulation %PE only; multi-form aggregate required)"
        else:
            overall = "PASS" if overall_raw else "FAIL"

        mean_abs = pp.get("mean_abs_%PE")
        mean_abs_str = "N/A" if mean_abs is None else f"{float(mean_abs):.2f}%"

        lines = [
            "IVIVC Level A Analysis",
            "======================",
            f"Method: {self.method}",
            f"Study: {self.study_label or 'N/A'}",
            "",
            "Levy Plot (IVIVC correlation)",
            "---------------------------",
            f"Slope: {lp.get('slope', float('nan')):.4f}",
            f"Intercept: {lp.get('intercept', float('nan')):.4f}",
            f"R-squared: {lp.get('r_squared', float('nan')):.4f}",
            f"N points (0.05-0.95): {len(lp.get('x', []))}",
            "",
            "Predictability Assessment (FDA 1997)",
            "-------------------------------------",
            f"Cmax %PE: {pp.get('%PE_Cmax', float('nan')):.2f}% (formulation limit <= 15%)",
            f"AUCinf %PE: {pp.get('%PE_AUC', float('nan')):.2f}% (formulation limit <= 15%)",
            f"Cross-form mean abs %PE: {mean_abs_str} (FDA limit <= 10% per metric)",
            f"Overall: {overall}",
            "",
            f"Disclaimer: {_DISCLAIMER}",
        ]
        return "\n".join(lines)

    def report(
        self,
        output_path: str | Path,
        format: str = "html",
    ) -> str | bytes:
        """Generate a report for this IVIVC result.

        Parameters
        ----------
        output_path : str | Path
            Where to save the report file.
        format : str, optional
            Output format: ``"html"``, ``"markdown"``, ``"pdf"``, or ``"docx"``.

        Returns
        -------
        str | bytes
            Rendered content (str for html/markdown, bytes for pdf/docx).
        """
        from .reporting import report_ivivc

        return report_ivivc(output_path=output_path, format=format, result=self)

    def plot(
        self,
        output_path: str | Path | None = None,
        show: bool = False,
    ) -> None:
        """Plot the IVIVC figure with four panels.

        Panels: (1) Fraction absorbed over time, (2) Levy plot with regression,
        (3) Predicted vs observed overlay, (4) In vitro dissolution profile.

        Parameters
        ----------
        output_path : str or Path or None, optional
            If provided, saves the figure to this path (PNG/PDF/SVG).
        show : bool, optional
            If True, calls plt.show() to display interactively. Default False.
        """
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(2, 2, figsize=(10, 8), dpi=600)

        # Panel 1: Fraction absorbed vs time
        ax = axes[0, 0]
        ax.plot(self.times, self.fa, "o-", color="#003366", linewidth=2, markersize=5)
        ax.plot(
            self.ivt_times,
            self.ivt_fraction,
            "s--",
            color="#cc3300",
            linewidth=1.5,
            markersize=4,
            label="In vitro fraction dissolved",
        )
        ax.set_title("Fraction Absorbed vs Dissolved", fontsize=10)
        ax.set_xlabel("Time (h)", fontsize=9)
        ax.set_ylabel("Fraction", fontsize=9)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 1.1)

        # Panel 2: Levy plot
        ax = axes[0, 1]
        lp = self.levy_plot
        ax.scatter(lp["x"], lp["y"], color="#003366", s=30, zorder=3)
        if len(lp.get("x", [])) > 1:
            x_line = np.linspace(0, 1, 100)
            y_line = lp["slope"] * x_line + lp["intercept"]
            ax.plot(
                x_line,
                y_line,
                "-",
                color="#cc3300",
                linewidth=1.5,
                label=f"y={lp['slope']:.3f}x+{lp['intercept']:.3f}\nR2={lp['r_squared']:.3f}",
            )
            ax.plot([0, 1], [0, 1], ":", color="#888888", linewidth=1, label="1:1 line")
        ax.set_title("Levy Plot (IVIVC)", fontsize=10)
        ax.set_xlabel("In vitro fraction dissolved", fontsize=9)
        ax.set_ylabel("In vivo fraction absorbed", fontsize=9)
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, 1.05)
        ax.set_ylim(0, 1.05)

        # Panel 3: Predicted vs observed overlay
        ax = axes[1, 0]
        ax.plot(
            self.times,
            self.concentrations,
            "o-",
            color="#003366",
            linewidth=2,
            markersize=5,
            label="Observed",
        )
        ax.plot(
            self.predicted_times,
            self.predicted_concs,
            "--",
            color="#cc3300",
            linewidth=1.5,
            label="Predicted (IVIVC)",
        )
        ax.set_title("Predicted vs Observed Profile", fontsize=10)
        ax.set_xlabel("Time (h)", fontsize=9)
        ax.set_ylabel("Concentration", fontsize=9)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

        # Panel 4: In vitro dissolution
        ax = axes[1, 1]
        ax.plot(
            self.ivt_times,
            self.ivt_fraction * 100,
            "o-",
            color="#006699",
            linewidth=2,
            markersize=5,
        )
        ax.set_title("In Vitro Dissolution Profile", fontsize=10)
        ax.set_xlabel("Time (min)", fontsize=9)
        ax.set_ylabel("Cumulative % Dissolved", fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 105)

        fig.tight_layout()

        if output_path is not None:
            fig.savefig(output_path, bbox_inches="tight")
        if show:
            plt.show()
        plt.close(fig)

    def to_dict(self) -> dict[str, Any]:
        """Return a plain-dict representation for serialisation.

        Returns
        -------
        dict[str, Any]
        """
        return {
            "method": self.method,
            "study_label": self.study_label,
            "times": self.times.tolist(),
            "concentrations": self.concentrations.tolist(),
            "fa": self.fa.tolist(),
            "levy_plot_slope": self.levy_plot.get("slope"),
            "levy_plot_intercept": self.levy_plot.get("intercept"),
            "levy_plot_r_squared": self.levy_plot.get("r_squared"),
            "ivt_times": self.ivt_times.tolist(),
            "ivt_fraction": self.ivt_fraction.tolist(),
            "predicted_times": self.predicted_times.tolist(),
            "predicted_concs": self.predicted_concs.tolist(),
            "predictability": dict(self.predictability),
        }
