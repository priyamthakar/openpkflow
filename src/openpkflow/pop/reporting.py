"""Population PK report generation -- HTML, Markdown, PDF, DOCX."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .gof import GOFResult
    from .vpc import VPCResult

_DISCLAIMER = (
    "This report was generated using OpenPKFlow (open-source). "
    "Final regulatory interpretation should be reviewed by qualified "
    "pharmacokinetic and regulatory experts."
)

_MAX_TABLE_ROWS = 200


def report_gof(
    result: GOFResult,
    *,
    output_path: str | Path,
    format: str = "html",
) -> str | bytes:
    """Generate a GOF report in the requested format.

    Parameters
    ----------
    result : GOFResult
        Computed GOF result.
    output_path : str | Path
        Where to save the report.
    format : str, optional
        ``"html"``, ``"markdown"``, ``"pdf"``, or ``"docx"``. Default ``"html"``.

    Returns
    -------
    str | bytes
        Rendered content.

    Raises
    ------
    ValueError
        If format is not recognized.
    ImportError
        If PDF or DOCX is requested but ``openpkflow[reports]`` is not installed.
    """
    output_path = Path(output_path)
    fmt = format.lower().lstrip(".")

    if fmt == "html":
        return _gof_html(result, output_path)
    if fmt in ("md", "markdown"):
        return _gof_markdown(result, output_path)
    if fmt == "pdf":
        from openpkflow.report.pdf import render_gof_pdf_report

        return render_gof_pdf_report(result=result, output_path=output_path)
    if fmt == "docx":
        from openpkflow.report.docx import render_gof_docx_report

        return render_gof_docx_report(result=result, output_path=output_path)
    raise ValueError(f"Unknown format '{format}'. Choose from: html, markdown, pdf, docx.")


def report_vpc(
    result: VPCResult,
    *,
    output_path: str | Path,
    format: str = "html",
) -> str | bytes:
    """Generate a VPC report in the requested format.

    Parameters
    ----------
    result : VPCResult
        Computed VPC result.
    output_path : str | Path
        Where to save the report.
    format : str, optional
        ``"html"``, ``"markdown"``, ``"pdf"``, or ``"docx"``. Default ``"html"``.

    Returns
    -------
    str | bytes
        Rendered content.
    """
    output_path = Path(output_path)
    fmt = format.lower().lstrip(".")

    if fmt == "html":
        return _vpc_html(result, output_path)
    if fmt in ("md", "markdown"):
        return _vpc_markdown(result, output_path)
    if fmt == "pdf":
        from openpkflow.report.pdf import render_vpc_pdf_report

        return render_vpc_pdf_report(result=result, output_path=output_path)
    if fmt == "docx":
        from openpkflow.report.docx import render_vpc_docx_report

        return render_vpc_docx_report(result=result, output_path=output_path)
    raise ValueError(f"Unknown format '{format}'. Choose from: html, markdown, pdf, docx.")


# ---------------------------------------------------------------------------
# HTML renderers
# ---------------------------------------------------------------------------


def _gof_html(result: GOFResult, output_path: Path) -> str:
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    from .plotting import gof_plots_b64

    templates_dir = Path(__file__).parent.parent / "report" / "templates"
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html"]),
    )
    env.globals["zip"] = zip

    template = env.get_template("pop_gof_report.html")

    pm = result.pred_metrics()
    im = result.ipred_metrics()
    iwres_arr = result.iwres.tolist()

    @dataclass
    class _Row:
        id: str
        time: float
        dv: float
        pred: float
        ipred: float
        iwres: float

    rows = [
        _Row(
            id=str(result.id[i]),
            time=float(result.time[i]),
            dv=float(result.dv[i]),
            pred=float(result.pred[i]),
            ipred=float(result.ipred[i]),
            iwres=float(iwres_arr[i]),
        )
        for i in range(min(len(result.dv), _MAX_TABLE_ROWS))
    ]

    title = "Population PK GOF Report"
    if result.study_label:
        title += f" -- {result.study_label}"

    html = template.render(
        title=title,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        n_obs=len(result.dv),
        sigma=result.sigma,
        pred_rmse=pm["RMSE"],
        ipred_rmse=im["RMSE"],
        pred_r2=pm["R2"] if not math.isnan(pm["R2"]) else 0.0,
        ipred_r2=im["R2"] if not math.isnan(im["R2"]) else 0.0,
        pred_metrics=pm,
        ipred_metrics=im,
        plot_b64=gof_plots_b64(result),
        rows=rows,
        warnings=result.warnings,
    )

    output_path.write_text(html, encoding="utf-8")
    return html


def _vpc_html(result: VPCResult, output_path: Path) -> str:
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    from .plotting import vpc_plot_b64

    templates_dir = Path(__file__).parent.parent / "report" / "templates"
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html"]),
    )
    env.globals["zip"] = zip
    env.globals["range"] = range

    template = env.get_template("pop_vpc_report.html")

    title = "Visual Predictive Check (VPC)"
    if result.study_label:
        title += f" -- {result.study_label}"

    html = template.render(
        title=title,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        n_obs=len(result.obs_times),
        n_replicates=result.n_replicates,
        n_bins=result.n_bins,
        pi_lo=int(result.pi[0]),
        pi_med=int(result.pi[1]),
        pi_hi=int(result.pi[2]),
        bin_mids=result.bin_mids,
        obs_lower=result.obs_lower,
        obs_median=result.obs_median,
        obs_upper=result.obs_upper,
        sim_lower=result.sim_lower,
        sim_median=result.sim_median,
        sim_upper=result.sim_upper,
        plot_b64=vpc_plot_b64(result),
        warnings=result.warnings,
    )

    output_path.write_text(html, encoding="utf-8")
    return html


# ---------------------------------------------------------------------------
# Markdown renderers
# ---------------------------------------------------------------------------


def _gof_markdown(result: GOFResult, output_path: Path) -> str:
    pm = result.pred_metrics()
    im = result.ipred_metrics()

    def _f(v: float) -> str:
        return f"{v:.4g}" if not math.isnan(v) else "N/A"

    title = "Population PK GOF Report"
    if result.study_label:
        title += f" -- {result.study_label}"

    lines = [
        f"# {title}",
        "",
        f"Generated by OpenPKFlow | {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Summary Metrics",
        "",
        f"- N observations: {len(result.dv)}",
        f"- Sigma (proportional CV): {result.sigma}",
        "",
        "| Metric | OBS vs PRED | OBS vs IPRED |",
        "|--------|------------|--------------|",
        f"| N      | {int(pm['n'])} | {int(im['n'])} |",
        f"| MPE    | {_f(pm['MPE'])} | {_f(im['MPE'])} |",
        f"| RMSE   | {_f(pm['RMSE'])} | {_f(im['RMSE'])} |",
        f"| rRMSE% | {_f(pm['rRMSE_pct'])} | {_f(im['rRMSE_pct'])} |",
        f"| R2     | {_f(pm['R2'])} | {_f(im['R2'])} |",
        "",
    ]

    if result.warnings:
        lines += ["## Warnings", ""]
        for w in result.warnings:
            lines.append(f"- {w}")
        lines.append("")

    lines += ["---", f"*{_DISCLAIMER}*"]
    md = "\n".join(lines)
    output_path.write_text(md, encoding="utf-8")
    return md


def _vpc_markdown(result: VPCResult, output_path: Path) -> str:
    title = "Visual Predictive Check (VPC)"
    if result.study_label:
        title += f" -- {result.study_label}"

    pi = result.pi
    lines = [
        f"# {title}",
        "",
        f"Generated by OpenPKFlow | {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## VPC Settings",
        "",
        f"- N observed: {len(result.obs_times)}",
        f"- N replicates: {result.n_replicates}",
        f"- N bins: {result.n_bins}",
        f"- Percentiles: {pi[0]:.0f} / {pi[1]:.0f} / {pi[2]:.0f}",
        "",
        "## VPC Band Data",
        "",
        f"| Bin Mid | Obs {pi[0]:.0f}th | Obs {pi[1]:.0f}th | Obs {pi[2]:.0f}th "
        f"| Sim {pi[0]:.0f}th | Sim {pi[1]:.0f}th | Sim {pi[2]:.0f}th |",
        "|---------|---------|---------|---------|---------|---------|---------|",
    ]

    def _fv(v: float) -> str:
        return f"{v:.3g}" if not math.isnan(v) else "---"

    for i, mid in enumerate(result.bin_mids):
        lines.append(
            f"| {mid:.2f} | {_fv(result.obs_lower[i])} | {_fv(result.obs_median[i])} "
            f"| {_fv(result.obs_upper[i])} | {_fv(result.sim_lower[i])} "
            f"| {_fv(result.sim_median[i])} | {_fv(result.sim_upper[i])} |"
        )

    lines += ["", "---", f"*{_DISCLAIMER}*"]
    md = "\n".join(lines)
    output_path.write_text(md, encoding="utf-8")
    return md
