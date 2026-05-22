"""PK simulation report renderers: HTML, Markdown, PDF, and DOCX."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from openpkflow import __version__

if TYPE_CHECKING:
    from openpkflow.sim.results import SimulationResult

_DISCLAIMER = (
    "This report was generated using OpenPKFlow -- an open-source Python workflow "
    "for pharmacometric analysis. Final regulatory interpretation should be reviewed "
    "by qualified formulation, pharmacokinetic, and regulatory experts."
)

TEMPLATES_DIR = Path(__file__).parent.parent / "report" / "templates"


def report_simulation(
    result: SimulationResult,
    *,
    output_path: str | Path | None = None,
    format: str = "html",
    time_unit: str = "h",
    conc_unit: str = "ng/mL",
) -> str | bytes:
    """Generate a PK simulation report.

    Parameters
    ----------
    result : SimulationResult
        Simulation result to render.
    output_path : str | Path or None, optional
        If given, write the rendered report to this path.
    format : str, optional
        Output format: "html", "markdown", "pdf", or "docx".
        Defaults to "html". PDF and DOCX require openpkflow[reports].
    time_unit : str, optional
        Time unit label for plots and tables.
    conc_unit : str, optional
        Concentration unit label for plots and tables.

    Returns
    -------
    str | bytes
        Rendered report content.

    Raises
    ------
    ValueError
        For unknown format strings.
    """
    kw = {"output_path": output_path, "time_unit": time_unit, "conc_unit": conc_unit}
    if format == "markdown":
        return _sim_markdown(result, **kw)
    if format == "html":
        return _sim_html(result, **kw)
    if format == "pdf":
        from openpkflow.report.pdf import render_sim_pdf_report

        return render_sim_pdf_report(result=result, **kw)
    if format == "docx":
        from openpkflow.report.docx import render_sim_docx_report

        return render_sim_docx_report(result=result, **kw)
    raise ValueError(f"Unknown format {format!r}. Choose 'html', 'markdown', 'pdf', or 'docx'.")


# ---------------------------------------------------------------------------
# HTML renderer
# ---------------------------------------------------------------------------


def _sim_html(
    result: SimulationResult,
    *,
    output_path: str | Path | None = None,
    time_unit: str = "h",
    conc_unit: str = "ng/mL",
) -> str:
    from datetime import datetime, timezone

    import jinja2

    from openpkflow.sim.plotting import pk_profile_plot_b64

    model_name = type(result.model).__name__
    n_doses = len(result.regimen.doses)

    params = result.model.param_dict()

    dose_rows = [
        {"n": i + 1, "time": d.time, "amount": d.amount, "t_inf": d.t_inf}
        for i, d in enumerate(result.regimen.doses)
    ]

    # Limit data table to first 200 rows to keep HTML file manageable
    MAX_ROWS = 200
    data_rows = [
        {"time": f"{t:.4g}", "conc": f"{c:.4g}"}
        for t, c in zip(result.times[:MAX_ROWS], result.concs[:MAX_ROWS], strict=True)
    ]
    truncated = len(result.times) > MAX_ROWS

    plot_b64 = pk_profile_plot_b64(
        times=result.times,
        concs=result.concs,
        dose_times=result.regimen.dose_times,
        label=result.label,
        time_unit=time_unit,
        conc_unit=conc_unit,
    )

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
    )
    env.globals["zip"] = zip

    template = env.get_template("sim_report.html")

    rendered = template.render(
        title=f"PK Simulation Report{' -- ' + result.label if result.label else ''}",
        generated_at=datetime.now(timezone.utc).isoformat(),
        openpkflow_version=__version__,
        label=result.label or "N/A",
        model_name=model_name,
        route=result.regimen.route,
        n_doses=n_doses,
        t_start=result.times[0],
        t_end=result.times[-1],
        n_timepoints=len(result.times),
        Cmax=result.Cmax,
        Tmax=result.Tmax,
        Cmin=min(result.concs),
        Clast=result.concs[-1],
        params=params,
        dose_rows=dose_rows,
        data_rows=data_rows,
        truncated=truncated,
        warnings=result.warnings,
        plot_b64=plot_b64,
        time_unit=time_unit,
        conc_unit=conc_unit,
        disclaimer=_DISCLAIMER,
    )

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")

    return rendered


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------


def _sim_markdown(
    result: SimulationResult,
    *,
    output_path: str | Path | None = None,
    time_unit: str = "h",
    conc_unit: str = "ng/mL",
) -> str:
    from datetime import datetime, timezone

    generated_at = datetime.now(timezone.utc).isoformat()
    model_name = type(result.model).__name__

    lines: list[str] = [
        f"# PK Simulation Report{' -- ' + result.label if result.label else ''}",
        "",
        f"**Generated:** {generated_at}  ",
        f"**OpenPKFlow version:** {__version__}",
        "",
        "## Simulation Settings",
        "",
        "| Parameter | Value |",
        "|-----------|-------|",
        f"| Label | {result.label or 'N/A'} |",
        f"| Model | {model_name} |",
        f"| Route | {result.regimen.route} |",
        f"| Number of doses | {len(result.regimen.doses)} |",
        f"| Time range | {result.times[0]:.4g} to {result.times[-1]:.4g} {time_unit} |",
        "",
        "## Model Parameters",
        "",
        "| Parameter | Value |",
        "|-----------|-------|",
    ]
    for k, v in result.model.param_dict().items():
        val_str = f"{v:.4g}" if isinstance(v, float) else str(v)
        lines.append(f"| {k} | {val_str} |")

    lines += [
        "",
        "## Dose Regimen",
        "",
        "| # | Time | Amount |",
        "|---|------|--------|",
    ]
    for i, d in enumerate(result.regimen.doses):
        t_inf_str = f" (t_inf={d.t_inf:.4g})" if d.t_inf is not None else ""
        lines.append(f"| {i + 1} | {d.time:.4g} | {d.amount:.4g}{t_inf_str} |")

    lines += [
        "",
        "## Simulation Results",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Cmax | {result.Cmax:.4g} {conc_unit} |",
        f"| Tmax | {result.Tmax:.4g} {time_unit} |",
        f"| Cmin | {min(result.concs):.4g} {conc_unit} |",
        f"| Clast | {result.concs[-1]:.4g} {conc_unit} |",
    ]

    if result.warnings:
        lines += ["", "## Warnings", ""]
        for w in result.warnings:
            lines.append(f"- {w}")

    lines += [
        "",
        "---",
        "",
        f"*{_DISCLAIMER}*",
    ]

    content = "\n".join(lines)

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")

    return content
