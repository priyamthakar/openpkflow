"""NCA report renderers: per-subject and multi-subject summary."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from openpkflow import __version__

if TYPE_CHECKING:
    import jinja2

    from openpkflow.nca.results import NCAResult, NCASummaryResults

_DISCLAIMER = (
    "This report was generated using OpenPKFlow — an open-source Python workflow "
    "for pharmacometric analysis. Final regulatory interpretation should be reviewed "
    "by qualified formulation, pharmacokinetic, and regulatory experts."
)

TEMPLATES_DIR = Path(__file__).parent.parent / "report" / "templates"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fmt(v: float | None) -> str:
    """Format a float for report tables; return 'N/A' for None."""
    return f"{v:.4g}" if v is not None else "N/A"


def _cl_label(result: NCAResult) -> tuple[str, str]:
    """Return (label, value_str) for the clearance parameter."""
    if result.CL_F is not None:
        return "CL_F", _fmt(result.CL_F)
    if result.CL is not None:
        return "CL", _fmt(result.CL)
    return "CL", "N/A"


def _vz_label(result: NCAResult) -> tuple[str, str]:
    """Return (label, value_str) for the volume parameter."""
    if result.Vz_F is not None:
        return "Vz_F", _fmt(result.Vz_F)
    if result.Vz is not None:
        return "Vz", _fmt(result.Vz)
    return "Vz", "N/A"


# ---------------------------------------------------------------------------
# Single-subject report
# ---------------------------------------------------------------------------


def report_nca_single(
    result: NCAResult,
    *,
    output_path: str | Path | None = None,
    format: str = "html",
) -> str | bytes:
    """Generate a per-subject NCA report.

    Parameters
    ----------
    result : NCAResult
        NCA result for a single subject.
    output_path : str | Path or None, optional
        If given, write the rendered report to this path.
    format : str, optional
        Output format: ``"html"``, ``"markdown"``, ``"pdf"``, or ``"docx"``.
        Defaults to ``"html"``. PDF and DOCX require ``openpkflow[reports]``.

    Returns
    -------
    str | bytes
        Rendered report content.

    Raises
    ------
    ValueError
        For unknown format strings.
    """
    if format == "markdown":
        return _single_markdown(result, output_path=output_path)
    if format == "html":
        return _single_html(result, output_path=output_path)
    if format == "pdf":
        from openpkflow.report.pdf import render_nca_single_pdf_report

        return render_nca_single_pdf_report(result=result, output_path=output_path)
    if format == "docx":
        from openpkflow.report.docx import render_nca_single_docx_report

        return render_nca_single_docx_report(result=result, output_path=output_path)
    raise ValueError(f"Unknown format {format!r}. Choose 'html', 'markdown', 'pdf', or 'docx'.")


# ---------------------------------------------------------------------------
# Summary report
# ---------------------------------------------------------------------------


def report_nca_summary(
    summary: NCASummaryResults,
    *,
    output_path: str | Path | None = None,
    format: str = "html",
) -> str | bytes:
    """Generate a multi-subject NCA summary report.

    Parameters
    ----------
    summary : NCASummaryResults
        Collection of per-subject NCA results.
    output_path : str | Path or None, optional
        If given, write the rendered report to this path.
    format : str, optional
        Output format: ``"html"``, ``"markdown"``, ``"pdf"``, or ``"docx"``.
        Defaults to ``"html"``. PDF and DOCX require ``openpkflow[reports]``.

    Returns
    -------
    str | bytes
        Rendered report content.

    Raises
    ------
    ValueError
        For unknown format strings.
    """
    if format == "markdown":
        return _summary_markdown(summary, output_path=output_path)
    if format == "html":
        return _summary_html(summary, output_path=output_path)
    if format == "pdf":
        from openpkflow.report.pdf import render_nca_summary_pdf_report

        return render_nca_summary_pdf_report(summary=summary, output_path=output_path)
    if format == "docx":
        from openpkflow.report.docx import render_nca_summary_docx_report

        return render_nca_summary_docx_report(summary=summary, output_path=output_path)
    raise ValueError(f"Unknown format {format!r}. Choose 'html', 'markdown', 'pdf', or 'docx'.")


# ---------------------------------------------------------------------------
# Markdown renderers
# ---------------------------------------------------------------------------


def _single_markdown(
    result: NCAResult,
    *,
    output_path: str | Path | None = None,
) -> str:
    from datetime import datetime, timezone

    generated_at = datetime.now(timezone.utc).isoformat()
    cl_lbl, cl_val = _cl_label(result)
    vz_lbl, vz_val = _vz_label(result)

    lines: list[str] = [
        f"# NCA Report -- Subject {result.subject}",
        "",
        f"**Generated:** {generated_at}  ",
        f"**OpenPKFlow version:** {__version__}",
        "",
        "## Study Parameters",
        "",
        "| Parameter | Value |",
        "|-----------|-------|",
        f"| Subject | {result.subject} |",
        f"| Route | {result.route} |",
        f"| Dose | {result.dose} |",
        f"| AUC Method | {result.auc_method} |",
        f"| BLQ Method | {result.blq_method} |",
        "",
        "## PK Parameters",
        "",
        "| Parameter | Value |",
        "|-----------|-------|",
        f"| Cmax | {_fmt(result.Cmax)} |",
        f"| Tmax | {_fmt(result.Tmax)} |",
        f"| AUClast | {_fmt(result.AUClast)} |",
        f"| AUCinf_obs | {_fmt(result.AUCinf_obs)} |",
        f"| AUC_percent_extrapolated | {_fmt(result.AUC_percent_extrapolated)} |",
        f"| lambda_z | {_fmt(result.lambda_z)} |",
        f"| half_life | {_fmt(result.half_life)} |",
        f"| lambda_z_method | {result.lambda_z_method or 'N/A'} |",
        f"| {cl_lbl} | {cl_val} |",
        f"| {vz_lbl} | {vz_val} |",
        "",
    ]

    if result.warnings:
        lines.append("## Warnings")
        lines.append("")
        for w in result.warnings:
            lines.append(f"- {w}")
        lines.append("")

    lines += [
        "## Disclaimer",
        "",
        f"> {_DISCLAIMER}",
        "",
    ]

    rendered = "\n".join(lines)

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")

    return rendered


def _summary_markdown(
    summary: NCASummaryResults,
    *,
    output_path: str | Path | None = None,
) -> str:
    from datetime import datetime, timezone

    generated_at = datetime.now(timezone.utc).isoformat()

    lines: list[str] = [
        "# NCA Summary Report",
        "",
        f"**Generated:** {generated_at}  ",
        f"**OpenPKFlow version:** {__version__}",
        "",
    ]

    if summary.study_label:
        lines += [f"**Study:** {summary.study_label}", ""]

    lines += [
        "## Parameters",
        "",
        "| Subject | AUClast | AUCinf_obs | AUC%Extr |"
        " Cmax | Tmax | half_life | CL/CL_F | Vz/Vz_F |",
        "|---------|--------:|-----------:|---------:|"
        "-----:|-----:|----------:|--------:|--------:|",
    ]

    for r in summary.results:
        _, cl_val = _cl_label(r)
        _, vz_val = _vz_label(r)
        lines.append(
            f"| {r.subject} | {_fmt(r.AUClast)} | {_fmt(r.AUCinf_obs)} | "
            f"{_fmt(r.AUC_percent_extrapolated)} | {_fmt(r.Cmax)} | {_fmt(r.Tmax)} | "
            f"{_fmt(r.half_life)} | {cl_val} | {vz_val} |"
        )

    lines += [
        "",
        "## Disclaimer",
        "",
        f"> {_DISCLAIMER}",
        "",
    ]

    rendered = "\n".join(lines)

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")

    return rendered


# ---------------------------------------------------------------------------
# HTML renderers
# ---------------------------------------------------------------------------


def _make_jinja_env() -> jinja2.Environment:
    import jinja2

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
    )
    env.globals["zip"] = zip
    return env


def _single_html(
    result: NCAResult,
    *,
    output_path: str | Path | None = None,
) -> str:
    from datetime import datetime, timezone

    env = _make_jinja_env()
    template = env.get_template("nca_single_report.html")

    cl_lbl, cl_val = _cl_label(result)
    vz_lbl, vz_val = _vz_label(result)

    rendered = template.render(
        title=f"NCA Report -- Subject {result.subject}",
        generated_at=datetime.now(timezone.utc).isoformat(),
        openpkflow_version=__version__,
        result=result,
        cl_label=cl_lbl,
        cl_value=cl_val,
        vz_label=vz_lbl,
        vz_value=vz_val,
        disclaimer=_DISCLAIMER,
        fmt=_fmt,
    )

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")

    return rendered


def _summary_html(
    summary: NCASummaryResults,
    *,
    output_path: str | Path | None = None,
) -> str:
    from datetime import datetime, timezone

    env = _make_jinja_env()
    template = env.get_template("nca_summary_report.html")

    # Pre-compute per-row clearance/volume labels and values for the template
    rows = []
    for r in summary.results:
        cl_lbl, cl_val = _cl_label(r)
        vz_lbl, vz_val = _vz_label(r)
        rows.append(
            {
                "result": r,
                "cl_label": cl_lbl,
                "cl_value": cl_val,
                "vz_label": vz_lbl,
                "vz_value": vz_val,
            }
        )

    rendered = template.render(
        title="NCA Summary Report",
        generated_at=datetime.now(timezone.utc).isoformat(),
        openpkflow_version=__version__,
        study_label=summary.study_label,
        auc_method=summary.auc_method,
        blq_method=summary.blq_method,
        rows=rows,
        disclaimer=_DISCLAIMER,
        fmt=_fmt,
    )

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")

    return rendered
