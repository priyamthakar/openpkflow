"""NCA report renderers: per-subject and multi-subject summary."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import TYPE_CHECKING

from openpkflow import __version__

if TYPE_CHECKING:
    import jinja2

    from openpkflow.nca.results import NCAResult, NCASummaryResults
    from openpkflow.nca.sparse import SparseNCAResult

_DISCLAIMER = (
    "This report was generated using OpenPKFlow — an open-source Python workflow "
    "for pharmacometric analysis. Final regulatory interpretation should be reviewed "
    "by qualified formulation, pharmacokinetic, and regulatory experts."
)

_SPARSE_DISCLAIMER = (
    "This report was generated using OpenPKFlow (open-source). Final regulatory "
    "interpretation should be reviewed by qualified formulation, pharmacokinetic, "
    "and regulatory experts. Sparse NCA is a model-informed screening analysis and "
    "should not be used as a regulatory primary analysis without study-specific validation."
)

TEMPLATES_DIR = Path(__file__).parent.parent / "report" / "templates"


def report_sparse_nca(
    result: SparseNCAResult,
    *,
    output_path: str | Path | None = None,
    format: str = "html",
) -> str:
    """Generate a sparse-NCA screening report.

    Parameters
    ----------
    result : SparseNCAResult
        Model-informed sparse-NCA result.
    output_path : str | Path or None
        Optional destination path.
    format : str
        Output format: ``"html"`` or ``"markdown"``.

    Returns
    -------
    str
        Rendered report content.

    Raises
    ------
    ValueError
        If the format is unsupported.
    """
    if format == "markdown":
        rendered = _sparse_markdown(result)
    elif format == "html":
        rendered = _sparse_html(result)
    else:
        raise ValueError("Sparse NCA reports support only 'html' and 'markdown'.")
    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")
    return rendered


def _sparse_rows(result: SparseNCAResult) -> list[tuple[str, str, str]]:
    return [
        ("CL/F", _fmt(result.CL_F), "L/h"),
        ("Vz/F", _fmt(result.Vz_F), "L"),
        ("ka", _fmt(result.ka), "1/h"),
        ("Elimination rate", _fmt(result.k), "1/h"),
        ("Half-life", _fmt(result.half_life), "h"),
        ("AUClast", _fmt(result.AUClast), "concentration*h"),
        ("AUCinf", _fmt(result.AUCinf), "concentration*h"),
        ("Cmax", _fmt(result.Cmax), "concentration"),
        ("Tmax", _fmt(result.Tmax), "h"),
    ]


def _sparse_markdown(result: SparseNCAResult) -> str:
    status = "Converged" if result.converged else "Not converged"
    lines = [
        "# Sparse NCA Screening Report",
        "",
        f"**OpenPKFlow version:** {__version__}  ",
        f"**Subject:** {result.subject or 'Not specified'}  ",
        f"**Dose:** {result.dose:.4g} mg  ",
        f"**Samples:** {result.n_samples}  ",
        f"**Fit status:** {status}",
        "",
        "## Model-informed parameters",
        "",
        "| Parameter | Value | Unit |",
        "|---|---:|---|",
    ]
    lines.extend(f"| {name} | {value} | {unit} |" for name, value, unit in _sparse_rows(result))
    lines.extend(
        [
            "",
            "## Scope",
            "",
            "One-compartment oral model with first-order absorption fitted to sparse samples.",
            "",
            f"> {_SPARSE_DISCLAIMER}",
        ]
    )
    return "\n".join(lines)


def _sparse_html(result: SparseNCAResult) -> str:
    status = "Converged" if result.converged else "Not converged"
    parameter_rows = "".join(
        f"<tr><td>{escape(name)}</td><td>{escape(value)}</td><td>{escape(unit)}</td></tr>"
        for name, value, unit in _sparse_rows(result)
    )
    observed_rows = "".join(
        "<tr>"
        f"<td>{time:.4g}</td><td>{observed:.4g}</td><td>{fitted:.4g}</td>"
        f"<td>{observed - fitted:.4g}</td></tr>"
        for time, observed, fitted in zip(
            result.time_points or [],
            result.observed_conc or [],
            result.fitted_conc or [],
            strict=False,
        )
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sparse NCA Screening Report</title><style>
body{{font-family:Arial,sans-serif;color:#14213d;background:#f4f7fb;margin:0;padding:32px}}
main{{max-width:900px;margin:auto;background:white;padding:36px;border:1px solid #dce5ef}}
h1{{color:#0d3b66}}h2{{margin-top:28px;color:#0d3b66;font-size:18px}}
.meta{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}}
.card{{background:#eef5fb;padding:12px;border-left:3px solid #2a6f97}}
table{{width:100%;border-collapse:collapse;margin-top:12px}}
th,td{{padding:9px;border-bottom:1px solid #dce5ef;text-align:left}}
.disclaimer{{margin-top:28px;padding:14px;background:#fff7df;border-left:3px solid #d99b16;
font-size:13px;line-height:1.5}}
</style></head><body><main><h1>Sparse NCA Screening Report</h1>
<div class="meta"><div class="card"><strong>Subject</strong><br>
{escape(result.subject or "Not specified")}</div>
<div class="card"><strong>Dose</strong><br>{result.dose:.4g} mg</div>
<div class="card"><strong>Samples</strong><br>{result.n_samples}</div>
<div class="card"><strong>Fit status</strong><br>{status}</div></div>
<h2>Model-informed parameters</h2><table><thead><tr>
<th>Parameter</th><th>Value</th><th>Unit</th></tr></thead>
<tbody>{parameter_rows}</tbody></table>
<h2>Observed versus fitted</h2><table><thead><tr>
<th>Time</th><th>Observed</th><th>Fitted</th><th>Residual</th></tr></thead>
<tbody>{observed_rows}</tbody></table>
<h2>Scope</h2><p>One-compartment oral model with first-order absorption
fitted to sparse samples.</p>
<div class="disclaimer">{escape(_SPARSE_DISCLAIMER)}</div></main></body></html>"""


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
