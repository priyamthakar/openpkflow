"""Simulation-based Visual Predictive Check (VPC) for population PK."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import pandas as pd

    from openpkflow.sim.dosing import DoseRegimen
    from openpkflow.sim.models import OneCompartmentModel, TwoCompartmentModel


def _bin_percentiles(
    times: np.ndarray,
    values: np.ndarray,
    n_bins: int,
    pi: tuple[float, float, float],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Bin time-value pairs and compute percentiles within each bin.

    Parameters
    ----------
    times : np.ndarray
        Time values.
    values : np.ndarray
        Concentration values corresponding to each time.
    n_bins : int
        Number of time bins.
    pi : tuple[float, float, float]
        Percentile triple (lower, median, upper), e.g. (5.0, 50.0, 95.0).

    Returns
    -------
    tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]
        bin_mids, lower_pct, median_pct, upper_pct -- each length n_bins
        (bins with fewer than 2 observations are NaN).
    """
    edges = np.linspace(times.min(), times.max(), n_bins + 1)
    mids = (edges[:-1] + edges[1:]) / 2.0
    lower = np.full(n_bins, np.nan)
    median = np.full(n_bins, np.nan)
    upper = np.full(n_bins, np.nan)

    for i in range(n_bins):
        mask = (times >= edges[i]) & (times < edges[i + 1])
        if i == n_bins - 1:
            mask = (times >= edges[i]) & (times <= edges[i + 1])
        v = values[mask]
        if len(v) >= 2:
            lower[i] = np.percentile(v, pi[0])
            median[i] = np.percentile(v, pi[1])
            upper[i] = np.percentile(v, pi[2])

    return mids, lower, median, upper


@dataclass
class VPCResult:
    """Result of a simulation-based Visual Predictive Check.

    Parameters
    ----------
    bin_mids : list[float]
        Mid-points of each time bin.
    obs_lower : list[float]
        Observed lower percentile per bin.
    obs_median : list[float]
        Observed median per bin.
    obs_upper : list[float]
        Observed upper percentile per bin.
    sim_lower : list[float]
        Simulated lower percentile per bin (median across replicates).
    sim_median : list[float]
        Simulated median per bin.
    sim_upper : list[float]
        Simulated upper percentile per bin.
    obs_times : list[float]
        All observed time points (for scatter overlay).
    obs_dv : list[float]
        All observed DV values.
    pi : tuple[float, float, float]
        Percentile triple used. Default (5.0, 50.0, 95.0).
    n_bins : int
        Number of time bins used.
    n_replicates : int
        Number of simulation replicates used.
    study_label : str, optional
        Label shown in the report title.
    warnings : list[str]
        Any warnings generated during computation.
    """

    bin_mids: list[float]
    obs_lower: list[float]
    obs_median: list[float]
    obs_upper: list[float]
    sim_lower: list[float]
    sim_median: list[float]
    sim_upper: list[float]
    obs_times: list[float]
    obs_dv: list[float]
    pi: tuple[float, float, float] = (5.0, 50.0, 95.0)
    n_bins: int = 8
    n_replicates: int = 500
    study_label: str = ""
    warnings: list[str] = field(default_factory=list)

    def summary(self) -> str:
        """Return an ASCII text summary of the VPC result.

        Returns
        -------
        str
            Multi-line summary.
        """
        lines = ["Visual Predictive Check (VPC)", "============================="]
        if self.study_label:
            lines += [f"Study: {self.study_label}", ""]
        lines += [
            f"N observed  : {len(self.obs_times)}",
            f"N replicates: {self.n_replicates}",
            f"N bins      : {self.n_bins}",
            f"Percentiles : {self.pi[0]:.0f} / {self.pi[1]:.0f} / {self.pi[2]:.0f}",
        ]
        if self.warnings:
            lines += ["", "Warnings", "--------"]
            for w in self.warnings:
                lines.append(f"  - {w}")
        return "\n".join(lines)

    def plot(
        self,
        output_path: str | Path | None = None,
        show: bool = False,
    ) -> None:
        """Generate the VPC plot with observed scatter and simulation bands.

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

        from .plotting import _vpc_figure

        fig = _vpc_figure(self)
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
        """Generate a VPC report.

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
        from .reporting import report_vpc

        return report_vpc(self, output_path=output_path, format=format)


def simulate_vpc(
    model: OneCompartmentModel | TwoCompartmentModel,
    regimen: DoseRegimen,
    observed_df: pd.DataFrame,
    *,
    times: list[float] | None = None,
    sigma_proportional: float = 0.15,
    sigma_additive: float = 0.0,
    n_replicates: int = 500,
    seed: int | None = None,
    n_bins: int = 8,
    pi: tuple[float, float, float] = (5.0, 50.0, 95.0),
    time_col: str = "TIME",
    dv_col: str = "DV",
    study_label: str = "",
) -> VPCResult:
    """Compute a simulation-based VPC using the openpkflow sim engine.

    Simulates the deterministic PK profile, then adds proportional and/or
    additive residual variability across N replicates to generate percentile
    bands. Observed data percentiles are computed in the same time bins.

    Parameters
    ----------
    model : OneCompartmentModel | TwoCompartmentModel
        Fitted PK model parameters.
    regimen : DoseRegimen
        Dosing regimen used for simulation.
    observed_df : pd.DataFrame
        DataFrame containing observed concentrations (TIME, DV columns).
    times : list[float] or None, optional
        Time points for simulation. If None, uses observed TIME column.
    sigma_proportional : float, optional
        Proportional residual error (CV as fraction, e.g. 0.15 = 15%). Default 0.15.
    sigma_additive : float, optional
        Additive residual error (same units as DV). Default 0.0.
    n_replicates : int, optional
        Number of simulation replicates. Default 500.
    seed : int or None, optional
        Random seed for reproducibility.
    n_bins : int, optional
        Number of time bins for percentile computation. Default 8.
    pi : tuple[float, float, float], optional
        Percentile triple (lower, median, upper). Default (5.0, 50.0, 95.0).
    time_col : str, optional
        Time column name in observed_df. Default ``"TIME"``.
    dv_col : str, optional
        DV column name in observed_df. Default ``"DV"``.
    study_label : str, optional
        Label for the VPC report title.

    Returns
    -------
    VPCResult
        Computed percentile bands for observed and simulated data.

    Raises
    ------
    ValueError
        If observed_df is missing required columns.
    """

    from openpkflow.sim.simulate import simulate

    if time_col not in observed_df.columns or dv_col not in observed_df.columns:
        raise ValueError(
            f"observed_df must contain '{time_col}' and '{dv_col}' columns. "
            f"Available: {list(observed_df.columns)}"
        )

    obs_t = observed_df[time_col].to_numpy(dtype=float)
    obs_dv = observed_df[dv_col].to_numpy(dtype=float)

    sim_times = sorted(set(obs_t)) if times is None else sorted(times)

    base_result = simulate(model, regimen, sim_times)
    base_conc = np.array(base_result.concs)

    rng = np.random.default_rng(seed)
    all_sim_times: list[float] = []
    all_sim_conc: list[float] = []

    for _ in range(n_replicates):
        eps_prop = rng.normal(0.0, sigma_proportional, size=len(base_conc))
        if sigma_additive > 0:
            eps_add: float | np.ndarray = rng.normal(0.0, sigma_additive, size=len(base_conc))
        else:
            eps_add = 0.0
        sim_conc = base_conc * (1.0 + eps_prop) + eps_add
        sim_conc = np.maximum(sim_conc, 0.0)
        all_sim_times.extend(sim_times)
        all_sim_conc.extend(sim_conc.tolist())

    all_sim_t = np.array(all_sim_times)
    all_sim_c = np.array(all_sim_conc)

    # use the obs time range for binning
    t_min = float(min(np.min(obs_t), all_sim_t.min()))
    t_max = float(max(np.max(obs_t), all_sim_t.max()))

    # clip sim to [t_min, t_max] for binning
    edges = np.linspace(t_min, t_max, n_bins + 1)
    mids = (edges[:-1] + edges[1:]) / 2.0

    obs_lower_arr = np.full(n_bins, np.nan)
    obs_median_arr = np.full(n_bins, np.nan)
    obs_upper_arr = np.full(n_bins, np.nan)
    sim_lower_arr = np.full(n_bins, np.nan)
    sim_median_arr = np.full(n_bins, np.nan)
    sim_upper_arr = np.full(n_bins, np.nan)

    for i in range(n_bins):
        lo, hi = edges[i], edges[i + 1]
        obs_mask = (obs_t >= lo) & (obs_t <= hi)
        sim_mask = (all_sim_t >= lo) & (all_sim_t <= hi)
        ov = obs_dv[obs_mask]
        sv = all_sim_c[sim_mask]
        if len(ov) >= 2:
            obs_lower_arr[i] = np.percentile(ov, pi[0])
            obs_median_arr[i] = np.percentile(ov, pi[1])
            obs_upper_arr[i] = np.percentile(ov, pi[2])
        if len(sv) >= 2:
            sim_lower_arr[i] = np.percentile(sv, pi[0])
            sim_median_arr[i] = np.percentile(sv, pi[1])
            sim_upper_arr[i] = np.percentile(sv, pi[2])

    return VPCResult(
        bin_mids=mids.tolist(),
        obs_lower=obs_lower_arr.tolist(),
        obs_median=obs_median_arr.tolist(),
        obs_upper=obs_upper_arr.tolist(),
        sim_lower=sim_lower_arr.tolist(),
        sim_median=sim_median_arr.tolist(),
        sim_upper=sim_upper_arr.tolist(),
        obs_times=obs_t.tolist(),
        obs_dv=obs_dv.tolist(),
        pi=pi,
        n_bins=n_bins,
        n_replicates=n_replicates,
        study_label=study_label,
    )
