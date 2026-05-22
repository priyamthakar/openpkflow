"""MAP PK report renderers: HTML and Markdown."""

from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import TYPE_CHECKING

from openpkflow import __version__

if TYPE_CHECKING:
    from .results import MapPKResult

_DISCLAIMER = (
    "This report was generated using OpenPKFlow (open-source). "
    "Final regulatory interpretation should be reviewed by qualified "
    "formulation, pharmacokinetic, and regulatory experts."
)

TEMPLATES_DIR = Path(__file__).parent.parent / "report" / "templates"


def report_map_pk(
    result: MapPKResult,
    *,
    output_path: str | Path | None = None,
    format: str = "html",
) -> str | bytes:
    """Generate a MAP PK estimation report.

    Parameters
    ----------
    result : MapPKResult
        MAP estimation result to render.
    output_path : str or Path or None, optional
        If provided, write the rendered report to this path.
    format : str, optional
        Output format: "html", "markdown", "pdf", or "docx".

    Returns
    -------
    str | bytes
        Rendered content.

    Raises
    ------
    ValueError
        For unknown format strings.
    """
    if format == "html":
        content: str | bytes = _map_pk_html(result)
    elif format == "markdown":
        content = _map_pk_markdown(result)
    elif format in ("pdf", "docx"):
        raise NotImplementedError(
            f"format='{format}' for MAP PK reports is planned for v2.1.0. "
            "Use format='html' or format='markdown' for now."
        )
    else:
        raise ValueError(f"Unknown format '{format}'. Choose 'html' or 'markdown'.")

    if output_path is not None:
        mode = "wb" if isinstance(content, bytes) else "w"
        with open(output_path, mode, encoding=None if isinstance(content, bytes) else "utf-8") as f:
            f.write(content)

    return content


def _plot_b64(result: MapPKResult) -> str:
    """Return a base64-encoded PNG of the MAP profile plot."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from openpkflow.sim.methods import c_1cmt_iv_bolus, c_1cmt_oral

    t = np.array(result.time_points)
    t_dense = np.linspace(0, t[-1] * 1.5, 500) if len(t) > 0 else np.array([])

    fig, ax = plt.subplots(figsize=(7, 4), dpi=150)
    if len(t_dense) > 0:
        try:
            if result.route == "oral" and result.CL_F and result.Vz_F and result.ka:
                c_pred = c_1cmt_oral(t_dense, result.dose, result.CL_F, result.Vz_F, result.ka)
                ax.plot(t_dense, c_pred, "-", color="#0d3b66", linewidth=1.8, label="MAP fit")
            elif result.route == "iv_bolus" and result.CL and result.Vz:
                c_pred = c_1cmt_iv_bolus(t_dense, result.dose, result.CL, result.Vz)
                ax.plot(t_dense, c_pred, "-", color="#0d3b66", linewidth=1.8, label="MAP fit")
        except Exception:
            pass
    ax.scatter(result.time_points, result.observed_conc, color="#cc3300", s=40, zorder=5,
               label=f"Observed (n={result.n_observations})")
    ax.set_xlabel("Time (h)", fontsize=10)
    ax.set_ylabel("Concentration", fontsize=10)
    title = f"MAP Individual PK{' -- ' + result.subject if result.subject else ''}"
    ax.set_title(title, fontsize=11)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _map_pk_html(result: MapPKResult) -> str:
    """Render MAP PK result as an HTML report."""
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    env.globals["zip"] = zip
    tmpl = env.get_template("map_pk_report.html")

    plot_b64 = _plot_b64(result)

    def _fmt(v: float | None, decimals: int = 4) -> str:
        if v is None or (isinstance(v, float) and (v != v)):
            return "N/A"
        return f"{v:.{decimals}g}"

    obs_pred_rows = list(zip(result.time_points, result.observed_conc, result.predicted_conc))

    title = (
        f"MAP Individual PK -- {result.subject}"
        if result.subject
        else "MAP Individual PK Estimation"
    )

    return tmpl.render(
        title=title,
        result=result,
        plot_b64=plot_b64,
        fmt=_fmt,
        obs_pred_rows=obs_pred_rows,
        disclaimer=_DISCLAIMER,
        version=__version__,
        is_oral=result.route == "oral",
    )


def _map_pk_markdown(result: MapPKResult) -> str:
    """Render MAP PK result as a Markdown report."""
    title = (
        f"MAP Individual PK -- {result.subject}"
        if result.subject
        else "MAP Individual PK Estimation"
    )

    def _fmt(v: float | None) -> str:
        if v is None or (isinstance(v, float) and v != v):
            return "N/A"
        return f"{v:.4g}"

    lines = [
        f"# {title}",
        "",
        f"**Route:** {result.route}  |  **Dose:** {_fmt(result.dose)}  |  "
        f"**Observations:** {result.n_observations}",
        "",
        f"**Converged:** {'Yes' if result.converged else 'No'}  |  "
        f"**Uncertainty reliable:** {'Yes' if result.uncertainty_reliable else 'No'}  |  "
        f"**Gradient norm:** {result.gradient_norm:.3e}  |  "
        f"**Hessian cond.:** {result.condition_number:.2e}",
        "",
        "## MAP Parameters",
        "",
    ]

    if result.route == "oral":
        lines += [
            "| Parameter | Estimate | SE |",
            "|---|---|---|",
            f"| CL_F (L/h) | {_fmt(result.CL_F)} | {_fmt(result.CL_F_se)} |",
            f"| Vz_F (L) | {_fmt(result.Vz_F)} | {_fmt(result.Vz_F_se)} |",
            f"| ka (1/h) | {_fmt(result.ka)} | {_fmt(result.ka_se)} |",
        ]
    else:
        lines += [
            "| Parameter | Estimate | SE |",
            "|---|---|---|",
            f"| CL (L/h) | {_fmt(result.CL)} | {_fmt(result.CL_se)} |",
            f"| Vz (L) | {_fmt(result.Vz)} | {_fmt(result.Vz_se)} |",
        ]

    lines += [
        f"| k (1/h) | {_fmt(result.k)} | N/A |",
        f"| t1/2 (h) | {_fmt(result.half_life)} | N/A |",
        "",
        "## Derived PK Parameters",
        "",
        "| Parameter | Value |",
        "|---|---|",
        f"| AUCinf (h*conc) | {_fmt(result.AUCinf)} |",
        f"| Cmax (conc) | {_fmt(result.Cmax)} |",
        f"| Tmax (h) | {_fmt(result.Tmax)} |",
    ]

    if result.warnings:
        lines += ["", "## Warnings", ""]
        for w in result.warnings:
            lines.append(f"- **[!]** {w}")

    lines += [
        "",
        "## Observed vs Predicted",
        "",
        "| Time (h) | Observed | Predicted | Residual |",
        "|---|---|---|---|",
    ]
    for t, obs, pred in zip(result.time_points, result.observed_conc, result.predicted_conc):
        lines.append(f"| {t:.2f} | {obs:.4g} | {pred:.4g} | {obs - pred:.4g} |")

    lines += [
        "",
        "---",
        "",
        f"*{_DISCLAIMER}*",
        "",
        f"*Generated with OpenPKFlow v{__version__}*",
    ]

    return "\n".join(lines)
