"""Goodness-of-fit (GOF) metrics and results for population PK diagnostics."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import pandas as pd


def compute_iwres(
    dv: np.ndarray,
    ipred: np.ndarray,
    sigma: float = 1.0,
) -> np.ndarray:
    """Compute individual weighted residuals (IWRES) under a proportional error model.

    IWRES_i = (DV_i - IPRED_i) / (sigma * IPRED_i)

    Parameters
    ----------
    dv : np.ndarray
        Observed dependent variable values.
    ipred : np.ndarray
        Individual model predictions (IPRED).
    sigma : float, optional
        Proportional residual error coefficient (CV as fraction, e.g. 0.15 = 15%).
        Default 1.0 produces raw residuals divided by IPRED.

    Returns
    -------
    np.ndarray
        IWRES array of the same shape as dv.

    Raises
    ------
    ValueError
        If dv and ipred have different shapes or sigma <= 0.

    Notes
    -----
    Formula from Bauer (2019) NONMEM Users Guide Part V, Chapter 7.
    Degenerate: when dv == ipred, all IWRES == 0.
    """
    dv = np.asarray(dv, dtype=float)
    ipred = np.asarray(ipred, dtype=float)
    if dv.shape != ipred.shape:
        raise ValueError(
            f"dv and ipred must have the same shape. Got {dv.shape} and {ipred.shape}."
        )
    if sigma <= 0:
        raise ValueError(f"sigma must be > 0, got {sigma}.")

    with np.errstate(divide="ignore", invalid="ignore"):
        result = np.where(ipred != 0.0, (dv - ipred) / (sigma * ipred), 0.0)
    return result


def obs_pred_metrics(
    dv: np.ndarray,
    pred: np.ndarray,
) -> dict[str, float]:
    """Compute summary GOF metrics for OBS vs PRED.

    Parameters
    ----------
    dv : np.ndarray
        Observed values.
    pred : np.ndarray
        Model predictions (PRED or IPRED).

    Returns
    -------
    dict[str, float]
        Dictionary with keys: ``"n"``, ``"MPE"``, ``"RMSE"``, ``"rRMSE_pct"``, ``"R2"``.
        MPE is mean prediction error (bias). rRMSE is relative RMSE as percent.
        R2 is the coefficient of determination.

    Notes
    -----
    MPE = mean(DV - PRED) -- positive values indicate under-prediction.
    RMSE = sqrt(mean((DV - PRED)^2)).
    rRMSE_pct = 100 * RMSE / mean(DV).
    R2 = 1 - SS_res / SS_tot, where SS_tot uses mean(DV) as baseline.
    """
    dv = np.asarray(dv, dtype=float)
    pred = np.asarray(pred, dtype=float)
    residuals = dv - pred
    n = len(dv)
    mpe = float(np.mean(residuals))
    rmse = float(np.sqrt(np.mean(residuals**2)))
    mean_dv = float(np.mean(dv))
    rrmse = (100.0 * rmse / mean_dv) if mean_dv != 0.0 else float("nan")
    ss_res = float(np.sum(residuals**2))
    ss_tot = float(np.sum((dv - mean_dv) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot != 0.0 else float("nan")
    return {"n": float(n), "MPE": mpe, "RMSE": rmse, "rRMSE_pct": rrmse, "R2": r2}


@dataclass
class GOFResult:
    """Goodness-of-fit result for a population PK analysis.

    Holds OBS, PRED, IPRED, TIME, and ID arrays as delivered by the user
    (e.g. exported from NONMEM/nlmixr2). Provides IWRES computation,
    summary metrics, 4-panel GOF plots, and report generation.

    Parameters
    ----------
    dv : list[float]
        Observed concentrations.
    pred : list[float]
        Population predictions (PRED).
    ipred : list[float]
        Individual predictions (IPRED).
    time : list[float]
        Nominal time of each observation.
    id : list[str]
        Subject identifier for each observation.
    sigma : float
        Proportional residual error coefficient used for IWRES. Default 1.0.
    study_label : str, optional
        Label for the study (used in report title).
    warnings : list[str], optional
        Any warnings to surface in the report.
    """

    dv: list[float]
    pred: list[float]
    ipred: list[float]
    time: list[float]
    id: list[str]
    sigma: float = 1.0
    study_label: str = ""
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        n = len(self.dv)
        for attr in ("pred", "ipred", "time", "id"):
            if len(getattr(self, attr)) != n:
                raise ValueError(
                    f"All arrays must have the same length as dv ({n}). "
                    f"'{attr}' has length {len(getattr(self, attr))}."
                )

    @property
    def iwres(self) -> np.ndarray:
        """IWRES computed from IPRED under the proportional error model."""
        return compute_iwres(np.array(self.dv), np.array(self.ipred), self.sigma)

    def pred_metrics(self) -> dict[str, float]:
        """GOF metrics comparing DV vs PRED (population predictions).

        Returns
        -------
        dict[str, float]
            n, MPE, RMSE, rRMSE_pct, R2.
        """
        return obs_pred_metrics(np.array(self.dv), np.array(self.pred))

    def ipred_metrics(self) -> dict[str, float]:
        """GOF metrics comparing DV vs IPRED (individual predictions).

        Returns
        -------
        dict[str, float]
            n, MPE, RMSE, rRMSE_pct, R2.
        """
        return obs_pred_metrics(np.array(self.dv), np.array(self.ipred))

    def summary(self) -> str:
        """Return an ASCII text summary of GOF metrics.

        Returns
        -------
        str
            Multi-line summary with PRED and IPRED metrics.
        """
        pm = self.pred_metrics()
        im = self.ipred_metrics()

        def _f(v: float) -> str:
            return f"{v:.4g}" if not math.isnan(v) else "N/A"

        lines = [
            "Population PK GOF Summary",
            "=========================",
        ]
        if self.study_label:
            lines += [f"Study: {self.study_label}", ""]

        lines += [
            f"N observations : {int(pm['n'])}",
            f"Sigma (prop CV): {self.sigma}",
            "",
            "             PRED    IPRED",
            "  MPE      : " + _f(pm["MPE"]).rjust(8) + "  " + _f(im["MPE"]).rjust(8),
            "  RMSE     : " + _f(pm["RMSE"]).rjust(8) + "  " + _f(im["RMSE"]).rjust(8),
            "  rRMSE %  : " + _f(pm["rRMSE_pct"]).rjust(8) + "  " + _f(im["rRMSE_pct"]).rjust(8),
            "  R2       : " + _f(pm["R2"]).rjust(8) + "  " + _f(im["R2"]).rjust(8),
        ]

        if self.warnings:
            lines += ["", "Warnings", "--------"]
            for w in self.warnings:
                lines.append(f"  - {w}")

        return "\n".join(lines)

    def to_dataframe(self) -> pd.DataFrame:
        """Return a DataFrame with DV, PRED, IPRED, TIME, ID, and IWRES columns.

        Returns
        -------
        pd.DataFrame
            One row per observation.
        """
        import pandas as pd

        return pd.DataFrame(
            {
                "ID": self.id,
                "TIME": self.time,
                "DV": self.dv,
                "PRED": self.pred,
                "IPRED": self.ipred,
                "IWRES": list(self.iwres),
            }
        )

    def plot(
        self,
        output_path: str | Path | None = None,
        show: bool = False,
    ) -> None:
        """Generate a 4-panel GOF plot.

        Panels: OBS vs PRED, OBS vs IPRED, IWRES vs TIME, IWRES vs IPRED.

        Parameters
        ----------
        output_path : str or Path or None, optional
            If provided, saves the figure to this path.
        show : bool, optional
            If True, calls plt.show() to display interactively. Default False.
        """
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from .plotting import _gof_figure

        fig = _gof_figure(self)
        if output_path is not None:
            fig.savefig(output_path, bbox_inches="tight")
        if show:
            plt.show()
        plt.close(fig)

    def report(
        self,
        output_path: str | Path,
        *,
        format: str = "html",
    ) -> str | bytes:
        """Generate a GOF report.

        Parameters
        ----------
        output_path : str | Path
            Where to save the report.
        format : str, optional
            ``"html"``, ``"markdown"``, ``"pdf"``, or ``"docx"``. Default ``"html"``.

        Returns
        -------
        str | bytes
            Rendered content (str for html/markdown, bytes for pdf/docx).
        """
        from .reporting import report_gof

        return report_gof(self, output_path=output_path, format=format)
