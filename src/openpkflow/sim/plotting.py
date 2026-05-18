"""PK simulation profile plots — base64-encoded PNG for embedding in HTML reports."""

from __future__ import annotations

import base64
import io


def pk_profile_plot_b64(
    times: list[float],
    concs: list[float],
    dose_times: list[float] | None = None,
    label: str = "",
    time_unit: str = "h",
    conc_unit: str = "ng/mL",
) -> str:
    """Return a base64-encoded PNG of a PK concentration-time profile.

    Parameters
    ----------
    times : list[float]
        Simulation time points.
    concs : list[float]
        Simulated concentrations.
    dose_times : list[float] or None, optional
        Times at which doses were administered; vertical dashed lines are drawn.
    label : str, optional
        Profile label shown in the title.
    time_unit : str, optional
        Time axis label suffix, by default "h".
    conc_unit : str, optional
        Concentration axis label suffix, by default "ng/mL".

    Returns
    -------
    str
        ASCII base64-encoded PNG image string.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    t = np.array(times)
    c = np.array(concs)

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=110)

    ax.plot(t, c, color="#003366", linewidth=2, label=label or "Simulated profile")

    if dose_times:
        for i, td in enumerate(dose_times):
            ax.axvline(
                td,
                color="#cc3300",
                linestyle="--",
                linewidth=1.2,
                alpha=0.7,
                label="Dose" if i == 0 else None,
            )

    ax.set_xlabel(f"Time ({time_unit})", fontsize=11)
    ax.set_ylabel(f"Concentration ({conc_unit})", fontsize=11)
    title = f"PK Simulation Profile{' -- ' + label if label else ''}"
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")
