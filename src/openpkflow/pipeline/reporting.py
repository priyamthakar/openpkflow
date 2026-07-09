"""Multi-section pipeline report writer (HTML + Markdown)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

import jinja2

from openpkflow import __version__
from openpkflow.report.html import TEMPLATES_DIR

if TYPE_CHECKING:
    from openpkflow.pipeline.study import StudyPipelineResult

_DISCLAIMER = (
    "This report was generated using OpenPKFlow (open-source). Final regulatory "
    "interpretation should be reviewed by qualified formulation, pharmacokinetic, "
    "and regulatory experts."
)


def _fmt(value: float | None, digits: int = 4) -> str:
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.{digits}g}"
    except (TypeError, ValueError):
        return str(value)


def _build_context(result: StudyPipelineResult) -> dict[str, Any]:
    meta = result.metadata
    title = str(meta.get("title", "OpenPKFlow Study Report"))
    generated_at = str(meta.get("generated_at_utc") or datetime.now(timezone.utc).isoformat())
    version = str(meta.get("openpkflow_version", __version__))
    disclaimer = str(meta.get("disclaimer", _DISCLAIMER))

    nca_rows: list[dict[str, Any]] = []
    if result.nca is not None:
        for r in result.nca.results:
            cl_val = r.CL_F if r.CL_F is not None else r.CL
            vz_val = r.Vz_F if r.Vz_F is not None else r.Vz
            nca_rows.append(
                {
                    "subject": r.subject,
                    "AUClast": r.AUClast,
                    "AUCinf_obs": r.AUCinf_obs,
                    "Cmax": r.Cmax,
                    "Tmax": r.Tmax,
                    "half_life": r.half_life,
                    "cl": cl_val,
                    "vz": vz_val,
                    "AUC_percent_extrapolated": r.AUC_percent_extrapolated,
                    "warnings": list(r.warnings),
                }
            )

    return {
        "title": title,
        "generated_at": generated_at,
        "openpkflow_version": version,
        "disclaimer": disclaimer,
        "metadata": meta,
        "stages_requested": meta.get("stages_requested", []),
        "stages_completed": meta.get("stages_completed", []),
        "stage_status": meta.get("stage_status", {}),
        "warnings": meta.get("warnings", []),
        "methods": meta.get("methods", {}),
        "dissolution": result.dissolution,
        "nca": result.nca,
        "nca_rows": nca_rows,
        "be": result.be,
        "fmt": _fmt,
    }


def render_pipeline_html(result: StudyPipelineResult) -> str:
    """Render the multi-section pipeline HTML report.

    Parameters
    ----------
    result : StudyPipelineResult
        Completed pipeline result.

    Returns
    -------
    str
        Rendered HTML document.
    """
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
    )
    env.globals["zip"] = zip
    template = env.get_template("pipeline_report.html")
    return template.render(**_build_context(result))


def render_pipeline_markdown(result: StudyPipelineResult) -> str:
    """Render the multi-section pipeline Markdown report.

    Parameters
    ----------
    result : StudyPipelineResult
        Completed pipeline result.

    Returns
    -------
    str
        Markdown text (ASCII-safe for Windows consoles when printed).
    """
    ctx = _build_context(result)
    lines: list[str] = [
        f"# {ctx['title']}",
        "",
        f"- Generated (UTC): {ctx['generated_at']}",
        f"- OpenPKFlow version: {ctx['openpkflow_version']}",
        f"- Stages requested: {', '.join(ctx['stages_requested']) or 'none'}",
        f"- Stages completed: {', '.join(ctx['stages_completed']) or 'none'}",
        "",
    ]

    methods = ctx["methods"] or {}
    lines.extend(["## Methods", ""])
    for key, value in methods.items():
        if value is not None:
            lines.append(f"- {key}: {value}")
    lines.append("")

    stage_status = ctx["stage_status"] or {}
    if stage_status:
        lines.extend(["## Stage Status", ""])
        for name, status in stage_status.items():
            lines.append(f"- {name}: {status}")
        lines.append("")

    warnings = ctx["warnings"] or []
    if warnings:
        lines.extend(["## Warnings", ""])
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")

    d = result.dissolution
    if d is not None:
        lines.extend(
            [
                "## Dissolution Similarity",
                "",
                f"- Reference: {d.reference_label}",
                f"- Test: {d.test_label}",
                f"- Timepoints: {d.n_timepoints}",
                f"- f1: {d.f1_value:.4g}",
                f"- f2: {d.f2_value:.4g}",
                "",
            ]
        )
        if d.f2_value >= 50.0:
            lines.append("Interpretation: f2 >= 50 supports similarity between profiles.")
        else:
            lines.append("Interpretation: f2 < 50 does not support similarity between profiles.")
        lines.append("")
        lines.extend(
            [
                "| Time | Reference mean | Test mean |",
                "|------|----------------|-----------|",
            ]
        )
        for t, rm, tm in zip(d.time_points, d.reference_mean, d.test_mean, strict=False):
            lines.append(f"| {t} | {rm:.4g} | {tm:.4g} |")
        lines.append("")

    if result.nca is not None:
        lines.extend(
            [
                "## Non-Compartmental Analysis",
                "",
                f"- AUC method: {result.nca.auc_method}",
                f"- BLQ method: {result.nca.blq_method}",
                f"- Subjects: {len(result.nca.results)}",
                "",
                "| Subject | AUClast | AUCinf_obs | Cmax | Tmax | half_life | CL/CL_F |",
                "|---------|---------|------------|------|------|-----------|---------|",
            ]
        )
        for row in ctx["nca_rows"]:
            lines.append(
                f"| {row['subject']} | {_fmt(row['AUClast'])} | {_fmt(row['AUCinf_obs'])} | "
                f"{_fmt(row['Cmax'])} | {_fmt(row['Tmax'])} | {_fmt(row['half_life'])} | "
                f"{_fmt(row['cl'])} |"
            )
        lines.append("")

    b = result.be
    if b is not None:
        verdict = "BIOEQUIVALENT" if b.bioequivalent else "NOT BIOEQUIVALENT"
        lines.extend(
            [
                "## Bioequivalence (TOST)",
                "",
                f"- Parameter: {b.parameter}",
                f"- n: {b.n}",
                f"- GMR (T/R): {b.gmr:.4f}",
                f"- 90% CI: [{b.gmr_lower_90ci:.4f}, {b.gmr_upper_90ci:.4f}]",
                f"- Limits: [{b.be_lower:.2f}, {b.be_upper:.2f}]",
                f"- CV intra (%): {b.cv_intra_pct:.1f}",
                f"- Conclusion: {verdict}",
                "",
            ]
        )

    lines.extend(
        [
            "## Disclaimer",
            "",
            ctx["disclaimer"],
            "",
            f"*Generated by OpenPKFlow {ctx['openpkflow_version']}*",
            "",
        ]
    )
    return "\n".join(lines)


def report_pipeline(result: StudyPipelineResult, path: str | Path) -> Path:
    """Write a pipeline report; format inferred from file extension.

    Parameters
    ----------
    result : StudyPipelineResult
        Completed pipeline result.
    path : str or Path
        Output path. ``.md`` / ``.markdown`` -> Markdown; else HTML.

    Returns
    -------
    Path
        Resolved path written.
    """
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    suffix = out.suffix.lower()
    if suffix in (".md", ".markdown"):
        content = render_pipeline_markdown(result)
    else:
        content = render_pipeline_html(result)
    out.write_text(content, encoding="utf-8")
    return out.resolve()
