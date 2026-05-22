"""MAP PK and Bayesian BE report renderers: HTML and Markdown."""

from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import TYPE_CHECKING

from openpkflow import __version__

if TYPE_CHECKING:
    from .bayes_be import BayesBEResult
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
    ax.scatter(
        result.time_points,
        result.observed_conc,
        color="#cc3300",
        s=40,
        zorder=5,
        label=f"Observed (n={result.n_observations})",
    )
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

    obs_pred_rows = list(
        zip(result.time_points, result.observed_conc, result.predicted_conc, strict=False)
    )

    title = (
        f"MAP Individual PK -- {result.subject}"
        if result.subject
        else "MAP Individual PK Estimation"
    )

    return str(
        tmpl.render(
            title=title,
            result=result,
            plot_b64=plot_b64,
            fmt=_fmt,
            obs_pred_rows=obs_pred_rows,
            disclaimer=_DISCLAIMER,
            version=__version__,
            is_oral=result.route == "oral",
        )
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
    for t, obs, pred in zip(
        result.time_points, result.observed_conc, result.predicted_conc, strict=False
    ):
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


# ---------------------------------------------------------------------------
# Bayesian BE report
# ---------------------------------------------------------------------------


def report_bayes_be(
    result: BayesBEResult,
    *,
    output_path: str | Path | None = None,
    format: str = "html",
) -> str:
    """Generate a Bayesian BE report.

    Parameters
    ----------
    result : BayesBEResult
        Bayesian BE result to render.
    output_path : str or Path or None, optional
        If provided, write the rendered report to this path.
    format : str, optional
        "html" or "markdown".

    Returns
    -------
    str
        Rendered content.

    Raises
    ------
    ValueError
        For unknown format strings.
    """
    if format == "html":
        content: str = _bayes_be_html(result)
    elif format == "markdown":
        content = _bayes_be_markdown(result)
    else:
        raise ValueError(f"Unknown format '{format}'. Choose 'html' or 'markdown'.")

    if output_path is not None:
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(content)

    return content


def _gmr_posterior_b64(result: BayesBEResult) -> str:
    """Return base64-encoded PNG histogram of the GMR posterior."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, 3.5), dpi=150)
    ax.hist(
        result.gmr_posterior, bins=60, color="#1a78c2", alpha=0.75, density=True, label="Posterior"
    )
    ax.axvline(0.80, color="#dc2626", linewidth=1.5, linestyle="--", label="BE limits (0.80, 1.25)")
    ax.axvline(1.25, color="#dc2626", linewidth=1.5, linestyle="--")
    ax.axvline(
        result.gmr_mean,
        color="#0d3b66",
        linewidth=1.8,
        linestyle="-",
        label=f"Mean = {result.gmr_mean:.4g}",
    )
    lo, hi = result.gmr_95ci
    ax.axvspan(lo, hi, alpha=0.12, color="#1a78c2", label=f"95% CrI [{lo:.3g}, {hi:.3g}]")
    ax.set_xlabel("GMR (Test/Reference)", fontsize=10)
    ax.set_ylabel("Posterior density", fontsize=10)
    ax.set_title(f"GMR Posterior -- {result.metric}", fontsize=11)
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _bayes_be_html(result: BayesBEResult) -> str:
    """Render Bayesian BE result as HTML report."""
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    tmpl = env.get_template("bayes_be_report.html")

    plot_b64 = _gmr_posterior_b64(result)

    def _fmt(v: float | None, decimals: int = 4) -> str:
        if v is None or (isinstance(v, float) and v != v):
            return "N/A"
        return f"{v:.{decimals}g}"

    if result.p_be >= 0.95:
        be_verdict = "PASS"
        be_css = "ok"
    elif result.p_be >= 0.80:
        be_verdict = "BORDERLINE"
        be_css = "warn"
    else:
        be_verdict = "FAIL"
        be_css = "fail"

    title = f"Bayesian BE -- {result.metric}"

    return str(
        tmpl.render(
            title=title,
            result=result,
            plot_b64=plot_b64,
            fmt=_fmt,
            be_verdict=be_verdict,
            be_css=be_css,
            freq_be_str="PASS" if result.freq_be else "FAIL",
            freq_be_css="ok" if result.freq_be else "fail",
            disclaimer=_DISCLAIMER,
            version=__version__,
            be_lo=0.80,
            be_hi=1.25,
        )
    )


def _bayes_be_markdown(result: BayesBEResult) -> str:
    """Render Bayesian BE result as Markdown report."""
    title = f"Bayesian BE -- {result.metric}"

    def _fmt(v: float | None) -> str:
        if v is None or (isinstance(v, float) and v != v):
            return "N/A"
        return f"{v:.4g}"

    if result.p_be >= 0.95:
        decision = "**PASS**"
    elif result.p_be >= 0.80:
        decision = "**BORDERLINE**"
    else:
        decision = "**FAIL**"

    lines = [
        f"# {title}",
        "",
        f"**Subjects:** {result.n_subjects}  |  **MCMC samples:** {result.n_samples}",
        "",
        "## Bayesian Decision",
        "",
        "| Quantity | Value |",
        "|---|---|",
        f"| P(BE) = P(0.80 <= GMR <= 1.25) | {result.p_be:.3f} |",
        f"| Decision | {decision} |",
        f"| GMR (posterior mean) | {_fmt(result.gmr_mean)} |",
        f"| GMR 95% CrI | [{_fmt(result.gmr_95ci[0])}, {_fmt(result.gmr_95ci[1])}] |",
        f"| log(GMR) mean | {_fmt(result.beta_t_mean)} |",
        f"| log(GMR) 95% CrI | [{_fmt(result.beta_t_95ci[0])}, {_fmt(result.beta_t_95ci[1])}] |",
        f"| sigma_b (between-subject) | {_fmt(result.sigma_b_mean)} |",
        f"| sigma_w (within-subject) | {_fmt(result.sigma_w_mean)} |",
        "",
        "## Frequentist Reference (90% CI)",
        "",
        "| Quantity | Value |",
        "|---|---|",
        f"| GMR | {_fmt(result.freq_gmr)} |",
        f"| 90% CI | [{_fmt(result.freq_90ci[0])}, {_fmt(result.freq_90ci[1])}] |",
        f"| BE Decision | {'**PASS**' if result.freq_be else '**FAIL**'} |",
    ]

    if result.warnings:
        lines += ["", "## Warnings", ""]
        for w in result.warnings:
            lines.append(f"- **[!]** {w}")

    lines += [
        "",
        "---",
        "",
        f"*{_DISCLAIMER}*",
        "",
        f"*Generated with OpenPKFlow v{__version__}*",
    ]

    return "\n".join(lines)
