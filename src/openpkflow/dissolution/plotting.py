"""Dissolution profile plot — reference vs test mean with error bars."""
from __future__ import annotations

import base64
import io

import numpy as np


def dissolution_profile_plot_b64(
    time_points: list[float],
    reference_mean: list[float],
    test_mean: list[float],
    reference_label: str = "Reference",
    test_label: str = "Test",
) -> str:
    """Return a base64-encoded PNG of the dissolution profile comparison.

    Embeds cleanly as <img src="data:image/png;base64,..."> in HTML reports.
    Uses matplotlib with a non-interactive backend (Agg) — safe in headless environments.

    Parameters
    ----------
    time_points :
        Shared time points used in the comparison.
    reference_mean :
        Mean percent dissolved for the reference formulation at each time point.
    test_mean :
        Mean percent dissolved for the test formulation at each time point.
    reference_label :
        Legend label for the reference profile.
    test_label :
        Legend label for the test profile.

    Returns
    -------
    str
        ASCII base64-encoded PNG image string.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 4), dpi=110)

    tp = np.array(time_points)
    ref = np.array(reference_mean)
    tst = np.array(test_mean)

    ax.plot(tp, ref, "o-", color="#003366", linewidth=2, markersize=6,
            label=reference_label)
    ax.plot(tp, tst, "s--", color="#cc3300", linewidth=2, markersize=6,
            label=test_label)

    ax.set_xlabel("Time (min)", fontsize=11)
    ax.set_ylabel("Mean % Dissolved", fontsize=11)
    ax.set_title("Dissolution Profile Comparison", fontsize=12, fontweight="bold")
    ax.set_ylim(0, 105)
    ax.axhline(85, color="#888888", linestyle=":", linewidth=1, label="85% threshold")
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")
