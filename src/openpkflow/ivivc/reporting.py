"""IVIVC report rendering (Markdown and dispatch)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from openpkflow import __version__

if TYPE_CHECKING:
    from openpkflow.ivivc.results import IVIVCResult

_DISCLAIMER = (
    "This report was generated using OpenPKFlow -- an open-source Python workflow "
    "for pharmacometric analysis. Final regulatory interpretation should be reviewed "
    "by qualified formulation, pharmacokinetic, and regulatory experts."
)


def render_ivivc_markdown_report(
    *,
    result: IVIVCResult,
    output_path: str | Path | None = None,
) -> str:
    """Render an IVIVC Markdown report.

    Parameters
    ----------
    result : IVIVCResult
        The IVIVC result to render.
    output_path : str or Path or None, optional
        If given, write Markdown to this path.

    Returns
    -------
    str
        Rendered Markdown string.
    """
    generated_at = datetime.now(timezone.utc).isoformat()

    lp = result.levy_plot
    pp = result.predictability

    overall_raw = pp.get("overall_pass")
    if overall_raw is None:
        overall = "N/A (single-formulation)"
    else:
        overall = "PASS" if overall_raw else "FAIL"
    mean_abs = pp.get("mean_abs_%PE")
    mean_abs_str = "N/A" if mean_abs is None else f"{float(mean_abs):.2f}%"
    mean_status = "N/A" if mean_abs is None else ("PASS" if pp.get("passes_mean") else "FAIL")
    study_name = result.study_label or "IVIVC Level A"

    lines: list[str] = []
    lines.append(f"# IVIVC Level A Report: {study_name}")
    lines.append("")
    lines.append(f"**Generated:** {generated_at}")
    lines.append(f"**OpenPKFlow version:** {__version__}")
    lines.append("")

    lines.append("## Study Parameters")
    lines.append("")
    lines.append("| Parameter | Value |")
    lines.append("|-----------|-------|")
    lines.append(f"| Deconvolution method | {result.method} |")
    lines.append(f"| In vivo time points | {len(result.times)} |")
    lines.append(f"| Dissolution time points | {len(result.ivt_times)} |")
    lines.append("")

    lines.append("## Levy Plot (IVIVC Correlation)")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|------:|")
    lines.append(f"| Slope | {lp.get('slope', float('nan')):.4f} |")
    lines.append(f"| Intercept | {lp.get('intercept', float('nan')):.4f} |")
    lines.append(f"| R-squared | {lp.get('r_squared', float('nan')):.4f} |")
    lines.append(f"| N (0.05-0.95 range) | {len(lp.get('x', []))} |")
    lines.append("")

    lines.append("## Predictability Assessment (FDA 1997)")
    lines.append("")
    lines.append("| Metric | Value | Criterion | Status |")
    lines.append("|--------|------:|-----------|--------|")
    lines.append(
        f"| Cmax %PE | {pp.get('%PE_Cmax', float('nan')):.2f}% | <= 15% | "
        f"{'PASS' if pp.get('passes_cmax', False) else 'FAIL'} |"
    )
    lines.append(
        f"| AUCinf %PE | {pp.get('%PE_AUC', float('nan')):.2f}% | <= 15% | "
        f"{'PASS' if pp.get('passes_auc', False) else 'FAIL'} |"
    )
    lines.append(
        f"| Cross-form mean abs %PE | {mean_abs_str} | <= 10% per metric | {mean_status} |"
    )
    lines.append(f"| **Overall** | | | **{overall}** |")
    lines.append("")

    lines.append("## In Vivo Fraction Absorbed vs Time")
    lines.append("")
    # Show the first 15 rows
    n_show = min(15, len(result.times))
    lines.append("| Time (h) | Conc | F_a |")
    lines.append("|---------:|-----:|----:|")
    for i in range(n_show):
        t = result.times[i]
        c = result.concentrations[i]
        f = result.fa[i]
        lines.append(f"| {t:.2f} | {c:.4g} | {f:.4f} |")
    if len(result.times) > n_show:
        lines.append("| ... | ... | ... |")
        lines.append(f"*Showing first {n_show} of {len(result.times)} rows.*")
    lines.append("")

    lines.append("## Predicted vs Observed Comparison")
    lines.append("")
    n_pred_show = min(10, len(result.predicted_times))
    pred_step = max(1, len(result.predicted_times) // n_pred_show)
    pred_indices = range(0, len(result.predicted_times), pred_step)[:n_pred_show]
    lines.append("| Time (h) | Predicted Conc |")
    lines.append("|---------:|---------------:|")
    for i in pred_indices:
        t = result.predicted_times[i]
        c = result.predicted_concs[i]
        lines.append(f"| {t:.2f} | {c:.4g} |")
    lines.append("")

    lines.append("## Disclaimer")
    lines.append("")
    lines.append(f"> {_DISCLAIMER}")
    lines.append("")

    rendered = "\n".join(lines)

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")

    return rendered


def render_ivivc_html_report(
    *,
    result: IVIVCResult,
    output_path: str | Path | None = None,
) -> str:
    """Render an IVIVC HTML report.

    Parameters
    ----------
    result : IVIVCResult
        The IVIVC result to render.
    output_path : str or Path or None, optional
        If given, write HTML to this path.

    Returns
    -------
    str
        Rendered HTML string.
    """
    import base64
    import io

    import jinja2

    # Generate base64 plot
    import matplotlib

    from openpkflow.report.html import TEMPLATES_DIR

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    fig, axes = plt.subplots(2, 2, figsize=(10, 7), dpi=200)
    lp = result.levy_plot

    ax = axes[0, 0]
    ax.plot(result.times, result.fa, "o-", color="#003366", linewidth=2, markersize=5)
    ax.plot(
        result.ivt_times,
        result.ivt_fraction,
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

    ax = axes[0, 1]
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
            label=f"y={lp['slope']:.3f}x+{lp['intercept']:.3f}",
        )
        ax.plot([0, 1], [0, 1], ":", color="#888888", linewidth=1, label="1:1 line")
    ax.set_title("Levy Plot", fontsize=10)
    ax.set_xlabel("In vitro fraction dissolved", fontsize=9)
    ax.set_ylabel("In vivo fraction absorbed", fontsize=9)
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 1.05)
    ax.set_ylim(0, 1.05)

    ax = axes[1, 0]
    ax.plot(
        result.times,
        result.concentrations,
        "o-",
        color="#003366",
        linewidth=2,
        markersize=5,
        label="Observed",
    )
    ax.plot(
        result.predicted_times,
        result.predicted_concs,
        "--",
        color="#cc3300",
        linewidth=1.5,
        label="Predicted (IVIVC)",
    )
    ax.set_title("Predicted vs Observed", fontsize=10)
    ax.set_xlabel("Time (h)", fontsize=9)
    ax.set_ylabel("Concentration", fontsize=9)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    ax = axes[1, 1]
    ax.plot(
        result.ivt_times,
        result.ivt_fraction * 100,
        "o-",
        color="#006699",
        linewidth=2,
        markersize=5,
    )
    ax.set_title("Dissolution Profile", fontsize=10)
    ax.set_xlabel("Time (min)", fontsize=9)
    ax.set_ylabel("% Dissolved", fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 105)

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=200)
    plt.close(fig)
    buf.seek(0)
    plot_b64 = base64.b64encode(buf.read()).decode("utf-8")

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
    )
    env.globals["zip"] = zip

    template = env.get_template("ivivc_report.html")

    pp = result.predictability
    study_name = result.study_label or "IVIVC Level A"

    # Build data rows for table
    data_rows = []
    n_show = min(15, len(result.times))
    for i in range(n_show):
        data_rows.append(
            {
                "time": f"{result.times[i]:.2f}",
                "conc": f"{result.concentrations[i]:.4g}",
                "fa": f"{result.fa[i]:.4f}",
            }
        )

    pred_rows: list[dict[str, str]] = []
    n_pred_show = min(10, len(result.predicted_times))
    step = max(1, len(result.predicted_times) // n_pred_show)
    for i in range(0, len(result.predicted_times), step):
        if len(pred_rows) >= n_pred_show:
            break
        pred_rows.append(
            {
                "time": f"{result.predicted_times[i]:.2f}",
                "conc": f"{result.predicted_concs[i]:.4g}",
            }
        )

    mean_abs_pe = pp.get("mean_abs_%PE")
    rendered = template.render(
        title=f"IVIVC Level A Report: {study_name}",
        generated_at=datetime.now(timezone.utc).isoformat(),
        openpkflow_version=__version__,
        method=result.method,
        n_iv_timepoints=len(result.times),
        n_ivt_timepoints=len(result.ivt_times),
        levy_slope=f"{lp.get('slope', float('nan')):.4f}",
        levy_intercept=f"{lp.get('intercept', float('nan')):.4f}",
        levy_r_squared=f"{lp.get('r_squared', float('nan')):.4f}",
        levy_n=len(lp.get("x", [])),
        pe_cmax=f"{pp.get('%PE_Cmax', float('nan')):.2f}",
        pe_auc=f"{pp.get('%PE_AUC', float('nan')):.2f}",
        mean_abs_pe="N/A" if mean_abs_pe is None else f"{float(mean_abs_pe):.2f}",
        passes_cmax=pp.get("passes_cmax", False),
        passes_auc=pp.get("passes_auc", False),
        passes_mean=pp.get("passes_mean"),
        overall_pass=pp.get("overall_pass"),
        data_rows=data_rows,
        pred_rows=pred_rows,
        plot_b64=plot_b64,
        disclaimer=_DISCLAIMER,
    )

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")

    return rendered


def report_ivivc(
    *,
    output_path: str | Path,
    format: str = "html",
    result: IVIVCResult,
) -> str | bytes:
    """Generate an IVIVC report in the specified format.

    Parameters
    ----------
    output_path : str | Path
        Where to save the report file.
    format : str, optional
        ``"html"``, ``"markdown"``, ``"pdf"``, or ``"docx"``.
    result : IVIVCResult
        The IVIVC result to render.

    Returns
    -------
    str | bytes
        Rendered content.

    Raises
    ------
    ValueError
        If format is unknown.
    """
    if format == "html":
        return render_ivivc_html_report(result=result, output_path=output_path)
    if format == "markdown":
        return render_ivivc_markdown_report(result=result, output_path=output_path)
    if format == "pdf":
        from openpkflow.report.pdf import render_ivivc_pdf_report

        return render_ivivc_pdf_report(result=result, output_path=output_path)
    if format == "docx":
        from openpkflow.report.docx import render_ivivc_docx_report

        return render_ivivc_docx_report(result=result, output_path=output_path)
    raise ValueError(f"Unknown format {format!r}. Choose 'html', 'markdown', 'pdf', or 'docx'.")
