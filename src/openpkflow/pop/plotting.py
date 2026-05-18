"""Population PK diagnostic plots -- base64-encoded PNGs for report embedding."""

from __future__ import annotations

import base64
import io
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import matplotlib.figure

    from .gof import GOFResult
    from .vpc import VPCResult


def _gof_figure(result: GOFResult) -> matplotlib.figure.Figure:
    """Build the 4-panel GOF figure and return it (caller closes).

    Parameters
    ----------
    result : GOFResult
        Computed GOF result with DV/PRED/IPRED/TIME/IWRES data.

    Returns
    -------
    matplotlib.figure.Figure
        The composed figure -- caller is responsible for saving and closing.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    dv = np.array(result.dv)
    pred = np.array(result.pred)
    ipred = np.array(result.ipred)
    time = np.array(result.time)
    iwres = result.iwres

    fig, axes = plt.subplots(2, 2, figsize=(10, 8), dpi=600)

    # shared identity-line range
    lo = float(min(np.min(dv), np.min(pred), np.min(ipred)))
    hi = float(max(np.max(dv), np.max(pred), np.max(ipred)))
    pad = (hi - lo) * 0.05

    for ax, yvals, xlabel, ylabel, title in [
        (axes[0, 0], pred, "PRED", "OBS", "OBS vs PRED"),
        (axes[0, 1], ipred, "IPRED", "OBS", "OBS vs IPRED"),
    ]:
        ax.scatter(yvals, dv, alpha=0.6, s=20, color="#003366", edgecolors="none")
        ax.plot([lo - pad, hi + pad], [lo - pad, hi + pad], "r--", linewidth=1.2, label="Identity")
        ax.set_xlabel(xlabel, fontsize=10)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    # IWRES vs TIME
    axes[1, 0].scatter(time, iwres, alpha=0.6, s=20, color="#cc3300", edgecolors="none")
    axes[1, 0].axhline(0, color="black", linewidth=1.0, linestyle="--")
    axes[1, 0].axhline(2, color="#888888", linewidth=0.8, linestyle=":", label="+/-2")
    axes[1, 0].axhline(-2, color="#888888", linewidth=0.8, linestyle=":")
    axes[1, 0].set_xlabel("TIME", fontsize=10)
    axes[1, 0].set_ylabel("IWRES", fontsize=10)
    axes[1, 0].set_title("IWRES vs TIME", fontsize=11, fontweight="bold")
    axes[1, 0].legend(fontsize=8)
    axes[1, 0].grid(True, alpha=0.3)

    # IWRES vs IPRED
    axes[1, 1].scatter(ipred, iwres, alpha=0.6, s=20, color="#2a9d8f", edgecolors="none")
    axes[1, 1].axhline(0, color="black", linewidth=1.0, linestyle="--")
    axes[1, 1].axhline(2, color="#888888", linewidth=0.8, linestyle=":", label="+/-2")
    axes[1, 1].axhline(-2, color="#888888", linewidth=0.8, linestyle=":")
    axes[1, 1].set_xlabel("IPRED", fontsize=10)
    axes[1, 1].set_ylabel("IWRES", fontsize=10)
    axes[1, 1].set_title("IWRES vs IPRED", fontsize=11, fontweight="bold")
    axes[1, 1].legend(fontsize=8)
    axes[1, 1].grid(True, alpha=0.3)

    if result.study_label:
        fig.suptitle(f"GOF Diagnostics -- {result.study_label}", fontsize=13, fontweight="bold")

    fig.tight_layout()
    return fig


def _vpc_figure(result: VPCResult) -> matplotlib.figure.Figure:
    """Build the VPC figure and return it (caller closes).

    Parameters
    ----------
    result : VPCResult
        Computed VPC result with observed scatter and simulated bands.

    Returns
    -------
    matplotlib.figure.Figure
        The composed figure -- caller is responsible for saving and closing.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    mids = np.array(result.bin_mids)
    obs_t = np.array(result.obs_times)
    obs_dv = np.array(result.obs_dv)

    pi = result.pi
    fig, ax = plt.subplots(figsize=(9, 5), dpi=600)

    # Simulated bands
    ax.fill_between(
        mids,
        result.sim_lower,
        result.sim_upper,
        alpha=0.20,
        color="#457b9d",
        label=f"Sim {pi[0]:.0f}%-{pi[2]:.0f}% band",
    )
    ax.fill_between(
        mids,
        [m - (h - m) * 0.1 for m, h in zip(result.sim_median, result.sim_upper, strict=True)],
        [m + (h - m) * 0.1 for m, h in zip(result.sim_median, result.sim_upper, strict=True)],
        alpha=0.25,
        color="#e63946",
        label=f"Sim {pi[1]:.0f}% band",
    )

    # Simulated percentile lines
    ax.plot(mids, result.sim_lower, "--", color="#457b9d", linewidth=1.2)
    ax.plot(
        mids,
        result.sim_median,
        "-",
        color="#e63946",
        linewidth=1.5,
        label=f"Sim {pi[1]:.0f}th pctile",
    )
    ax.plot(mids, result.sim_upper, "--", color="#457b9d", linewidth=1.2)

    # Observed percentile lines
    ax.plot(
        mids,
        result.obs_lower,
        "v--",
        color="#003366",
        linewidth=1.2,
        markersize=5,
        label=f"Obs {pi[0]:.0f}th pctile",
    )
    ax.plot(
        mids,
        result.obs_median,
        "o-",
        color="#003366",
        linewidth=1.5,
        markersize=5,
        label=f"Obs {pi[1]:.0f}th pctile",
    )
    ax.plot(
        mids,
        result.obs_upper,
        "^--",
        color="#003366",
        linewidth=1.2,
        markersize=5,
        label=f"Obs {pi[2]:.0f}th pctile",
    )

    # Observed scatter
    ax.scatter(
        obs_t,
        obs_dv,
        alpha=0.35,
        s=15,
        color="#555555",
        edgecolors="none",
        zorder=2,
        label="Observed",
    )

    ax.set_xlabel("TIME", fontsize=11)
    ax.set_ylabel("Concentration", fontsize=11)
    title = "Visual Predictive Check (VPC)"
    if result.study_label:
        title += f"  --  {result.study_label}"
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_ylim(bottom=0)
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def gof_plots_b64(result: GOFResult) -> str:
    """Return a base64-encoded PNG of the 4-panel GOF plot.

    Parameters
    ----------
    result : GOFResult
        GOF result to plot.

    Returns
    -------
    str
        ASCII base64-encoded PNG image string.
    """
    fig = _gof_figure(result)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    import matplotlib.pyplot as plt

    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")


def vpc_plot_b64(result: VPCResult) -> str:
    """Return a base64-encoded PNG of the VPC plot.

    Parameters
    ----------
    result : VPCResult
        VPC result to plot.

    Returns
    -------
    str
        ASCII base64-encoded PNG image string.
    """
    fig = _vpc_figure(result)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    import matplotlib.pyplot as plt

    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")
