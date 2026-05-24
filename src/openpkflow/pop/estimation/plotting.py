"""Population PK diagnostic plot — 6-panel figure."""

from __future__ import annotations

import base64
from io import BytesIO
from typing import TYPE_CHECKING

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from .result import PopPKResult

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure


def pop_pk_figure(result: PopPKResult) -> Figure:
    """Build a 6-panel population PK diagnostic figure.

    Panels (2x3):
        1. OBS vs PRED  (all subjects)
        2. OBS vs IPRED (all subjects)
        3. CWRES vs TIME
        4. CWRES vs PRED
        5. EBE histogram per parameter
        6. EBE pairs scatter

    Parameters
    ----------
    result : PopPKResult
        Estimation result.

    Returns
    -------
    matplotlib.figure.Figure
    """
    fig, axes = plt.subplots(2, 3, figsize=(16, 10), dpi=150)
    fig.suptitle(
        f"Population PK Diagnostics — {result.method} ({result.route})",
        fontsize=14,
        fontweight="bold",
    )

    ax1, ax2, ax3 = axes[0]
    ax4, ax5, ax6 = axes[1]

    _panel_obs_vs_pred(ax1, result)
    _panel_obs_vs_ipred(ax2, result)
    _panel_cwres_vs_time(ax3, result)
    _panel_cwres_vs_pred(ax4, result)
    _panel_ebe_hist(ax5, result)
    _panel_ebe_pairs(ax6, result)

    fig.tight_layout(rect=(0, 0, 1, 0.96))
    return fig


def pop_pk_plot_b64(result: PopPKResult) -> str:
    """Render the diagnostic figure to a base64-encoded PNG string.

    Parameters
    ----------
    result : PopPKResult

    Returns
    -------
    str
        Base64-encoded PNG.
    """
    fig = pop_pk_figure(result)
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")


def _panel_obs_vs_pred(ax: Axes, result: PopPKResult) -> None:
    obs_all, pred_all = _collect_obs_pred(result)
    if len(obs_all) < 2:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        ax.set_xlabel("PRED")
        ax.set_ylabel("OBS")
        ax.set_title("OBS vs PRED")
        return
    ax.scatter(pred_all, obs_all, alpha=0.5, s=12, edgecolors="none")
    lim = max(np.max(pred_all), np.max(obs_all)) * 1.1
    ax.plot([0, lim], [0, lim], "k--", lw=0.8)
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_xlabel("PRED")
    ax.set_ylabel("OBS")
    ax.set_title("OBS vs PRED")


def _panel_obs_vs_ipred(ax: Axes, result: PopPKResult) -> None:
    obs_list: list[float] = []
    ipred_list: list[float] = []
    for subj in sorted(result.individual_predictions.keys()):
        obs_subj = result.observed_concentrations.get(subj, np.array([]))
        ipred_subj = result.individual_predictions.get(subj, np.array([]))
        n = min(len(obs_subj), len(ipred_subj))
        if n > 0:
            obs_list.extend(obs_subj[:n].tolist())
            ipred_list.extend(ipred_subj[:n].tolist())
    if len(obs_list) < 2:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        ax.set_xlabel("IPRED")
        ax.set_ylabel("OBS")
        ax.set_title("OBS vs IPRED")
        return
    obs_arr = np.array(obs_list)
    ipred_arr = np.array(ipred_list)
    ax.scatter(ipred_arr, obs_arr, alpha=0.5, s=12, edgecolors="none")
    lim = max(np.max(ipred_arr), np.max(obs_arr)) * 1.1
    ax.plot([0, lim], [0, lim], "k--", lw=0.8)
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_xlabel("IPRED")
    ax.set_ylabel("OBS")
    ax.set_title("OBS vs IPRED")


def _panel_cwres_vs_time(ax: Axes, result: PopPKResult) -> None:
    all_times: list[float] = []
    all_cwres: list[float] = []
    for subj in sorted(result.individual_predictions.keys()):
        t_subj = result.observed_times.get(subj, np.array([]))
        obs_subj = result.observed_concentrations.get(subj, np.array([]))
        ipred_subj = result.individual_predictions.get(subj, np.array([]))
        n = min(len(t_subj), len(obs_subj), len(ipred_subj))
        if n == 0:
            continue
        cwres_val = _compute_cwres(
            obs_subj[:n], ipred_subj[:n], result.sigma_prop, result.sigma_add
        )
        all_times.extend(t_subj[:n].tolist())
        all_cwres.extend(cwres_val.tolist())
    if len(all_times) < 2:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        ax.set_xlabel("TIME")
        ax.set_ylabel("CWRES")
        ax.set_title("CWRES vs TIME")
        return
    ax.scatter(all_times, all_cwres, alpha=0.5, s=12, edgecolors="none")
    ax.axhline(0, color="grey", lw=0.8)
    ax.axhline(2, color="grey", lw=0.5, ls=":")
    ax.axhline(-2, color="grey", lw=0.5, ls=":")
    ax.set_xlabel("TIME")
    ax.set_ylabel("CWRES")
    ax.set_title("CWRES vs TIME")


def _panel_cwres_vs_pred(ax: Axes, result: PopPKResult) -> None:
    obs_all, pred_all = _collect_obs_pred(result)
    if len(obs_all) < 2:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        ax.set_xlabel("PRED")
        ax.set_ylabel("CWRES")
        ax.set_title("CWRES vs PRED")
        return

    cwres_all: list[float] = []
    pred_matched: list[float] = []
    idx = 0
    for subj in sorted(result.individual_predictions.keys()):
        obs_subj = result.observed_concentrations.get(subj, np.array([]))
        ipred_subj = result.individual_predictions.get(subj, np.array([]))
        n = min(len(obs_subj), len(ipred_subj))
        if n == 0:
            continue
        if idx + n > len(pred_all):
            break
        cwres_val = _compute_cwres(
            obs_subj[:n], ipred_subj[:n], result.sigma_prop, result.sigma_add
        )
        cwres_all.extend(cwres_val.tolist())
        pred_matched.extend(pred_all[idx : idx + n].tolist())
        idx += n

    if len(cwres_all) < 2:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        ax.set_xlabel("PRED")
        ax.set_ylabel("CWRES")
        ax.set_title("CWRES vs PRED")
        return
    ax.scatter(pred_matched, cwres_all, alpha=0.5, s=12, edgecolors="none")
    ax.axhline(0, color="grey", lw=0.8)
    ax.axhline(2, color="grey", lw=0.5, ls=":")
    ax.axhline(-2, color="grey", lw=0.5, ls=":")
    ax.set_xlabel("PRED")
    ax.set_ylabel("CWRES")
    ax.set_title("CWRES vs PRED")


def _panel_ebe_hist(ax: Axes, result: PopPKResult) -> None:
    if result.ebe.empty or len(result.param_names) == 0:
        ax.text(0.5, 0.5, "No EBE data", ha="center", va="center", transform=ax.transAxes)
        ax.set_title("EBE Distributions")
        return
    param_names = result.param_names
    colors = ["steelblue", "darkorange", "forestgreen"]
    for i, pname in enumerate(param_names):
        col = f"eta_{pname}"
        if col not in result.ebe.columns:
            continue
        vals = result.ebe[col].dropna().values
        if len(vals) < 2:
            continue
        ax.hist(
            vals,
            bins=min(12, len(vals)),
            alpha=0.4,
            color=colors[i % len(colors)],
            label=pname,
            density=True,
        )
    ax.legend(fontsize=8, loc="upper right")
    ax.set_xlabel("eta")
    ax.set_ylabel("Density")
    ax.set_title("EBE Distributions")


def _panel_ebe_pairs(ax: Axes, result: PopPKResult) -> None:
    param_names = result.param_names
    if len(param_names) < 2 or result.ebe.empty:
        ax.text(0.5, 0.5, "Need >= 2 params", ha="center", va="center", transform=ax.transAxes)
        ax.set_title("EBE Pairs")
        return
    col_x = f"eta_{param_names[0]}"
    col_y = f"eta_{param_names[1]}"
    if col_x not in result.ebe.columns or col_y not in result.ebe.columns:
        ax.text(0.5, 0.5, "Missing EBE columns", ha="center", va="center", transform=ax.transAxes)
        ax.set_title("EBE Pairs")
        return
    n_min = min(len(result.ebe), 2)
    if n_min < 2:
        ax.text(0.5, 0.5, "Insufficient data", ha="center", va="center", transform=ax.transAxes)
        ax.set_title("EBE Pairs")
        return
    ax.scatter(
        result.ebe[col_x].values,
        result.ebe[col_y].values,
        alpha=0.6,
        s=16,
        edgecolors="none",
    )
    ax.axhline(0, color="grey", lw=0.5)
    ax.axvline(0, color="grey", lw=0.5)
    ax.set_xlabel(param_names[0])
    ax.set_ylabel(param_names[1])
    ax.set_title("EBE Pairs")


def _compute_cwres(
    obs: np.ndarray,
    ipred: np.ndarray,
    sigma_prop: float,
    sigma_add: float,
) -> np.ndarray:
    sd = np.sqrt((sigma_prop * np.abs(ipred) + 1e-9) ** 2 + sigma_add**2)
    return (obs - ipred) / (sd + 1e-9)


def _collect_obs_pred(
    result: PopPKResult,
) -> tuple[np.ndarray, np.ndarray]:
    obs_list: list[float] = []
    pred_list: list[float] = []
    pred_idx = 0
    for subj in sorted(result.individual_predictions.keys()):
        obs_subj = result.observed_concentrations.get(subj, np.array([]))
        n = len(obs_subj)
        if n == 0:
            continue
        obs_list.extend(obs_subj.tolist())
        if pred_idx + n <= len(result.population_predictions):
            pred_list.extend(result.population_predictions[pred_idx : pred_idx + n].tolist())
            pred_idx += n
    return np.array(obs_list, dtype=float), np.array(pred_list, dtype=float)
