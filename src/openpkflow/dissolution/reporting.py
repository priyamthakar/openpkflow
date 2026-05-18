from __future__ import annotations

from pathlib import Path

from openpkflow import __version__

_DISCLAIMER = (
    "This report was generated using OpenPKFlow (open-source). "
    "Final regulatory interpretation should be reviewed by qualified "
    "formulation, pharmacokinetic, and regulatory experts."
)


def render_markdown_report(
    *,
    title: str,
    reference_label: str,
    test_label: str,
    f1_value: float,
    f2_value: float,
    n_timepoints: int,
    time_points: list[float],
    reference_mean: list[float],
    test_mean: list[float],
    output_path: str | Path | None = None,
) -> str:
    """Render a dissolution comparison Markdown report.

    Parameters
    ----------
    title :
        Report title.
    reference_label :
        Label for the reference formulation.
    test_label :
        Label for the test formulation.
    f1_value :
        Computed f1 difference factor.
    f2_value :
        Computed f2 similarity factor.
    n_timepoints :
        Number of matched timepoints used in the calculation.
    time_points :
        Timepoint values for the data table.
    reference_mean :
        Mean percent dissolved values for the reference at each timepoint.
    test_mean :
        Mean percent dissolved values for the test at each timepoint.
    output_path :
        If given, write the rendered Markdown to this path (parent dirs
        created automatically).

    Returns
    -------
    str
        The rendered Markdown string.
    """
    from datetime import datetime, timezone

    generated_at = datetime.now(timezone.utc).isoformat()

    if f2_value >= 50:
        interpretation = (
            "f2 >= 50 supports similarity between the reference and test profiles."
        )
        f2_status = "PASS"
    else:
        interpretation = "f2 < 50 does not support similarity."
        f2_status = "FAIL"

    f1_status = "PASS" if f1_value <= 15 else "FAIL"

    lines: list[str] = []

    # -- Title and metadata ------------------------------------------
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"**Generated:** {generated_at}  ")
    lines.append(f"**OpenPKFlow version:** {__version__}")
    lines.append("")

    # -- Study parameters --------------------------------------------
    lines.append("## Study Parameters")
    lines.append("")
    lines.append("| Parameter | Value |")
    lines.append("|-----------|-------|")
    lines.append(f"| Reference | {reference_label} |")
    lines.append(f"| Test | {test_label} |")
    lines.append(f"| Timepoints (n) | {n_timepoints} |")
    lines.append("")

    # -- Results -----------------------------------------------------
    lines.append("## Similarity Factor Results")
    lines.append("")
    lines.append("| Parameter | Value | Criterion | Status |")
    lines.append("|-----------|------:|-----------|--------|")
    lines.append(
        f"| f1 (Difference Factor) | {f1_value:.2f} | 0 - 15 (acceptable) | {f1_status} |"
    )
    lines.append(
        f"| f2 (Similarity Factor) | {f2_value:.2f} | >= 50 (acceptable) | {f2_status} |"
    )
    lines.append("")
    lines.append(f"**Interpretation:** {interpretation}")
    lines.append("")

    # -- Data table --------------------------------------------------
    lines.append("## Dissolution Profile Data")
    lines.append("")
    lines.append(f"| Time (min) | {reference_label} Mean (%) | {test_label} Mean (%) | Difference (%) |")
    lines.append("|----------:|------------------:|---------------:|---------------:|")
    for t, r, ts in zip(time_points, reference_mean, test_mean):
        lines.append(f"| {t} | {r:.2f} | {ts:.2f} | {ts - r:.2f} |")
    lines.append("")

    # -- Disclaimer --------------------------------------------------
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


def report_dissolution(
    *,
    output_path: str | Path,
    format: str = "html",
    **kwargs: object,
) -> str | bytes:
    """Generate a dissolution comparison report in the specified format.

    Parameters
    ----------
    output_path :
        Where to save the report file.
    format :
        Output format: ``"html"``, ``"markdown"``, ``"pdf"``, or ``"docx"``.
    **kwargs :
        Keyword arguments forwarded to the underlying renderer.

    Returns
    -------
    str | bytes
        The rendered report content (str for html/markdown, bytes for pdf/docx).

    Raises
    ------
    ValueError
        If ``format`` is not a recognised format string.
    """
    if format == "html":
        from openpkflow.report.html import render_html_report

        return render_html_report(output_path=output_path, **kwargs)  # type: ignore[arg-type]

    if format == "markdown":
        return render_markdown_report(output_path=output_path, **kwargs)  # type: ignore[arg-type]

    if format == "pdf":
        from openpkflow.report.pdf import render_comparison_pdf_report

        return render_comparison_pdf_report(output_path=output_path, **kwargs)  # type: ignore[arg-type]

    if format == "docx":
        from openpkflow.report.docx import render_comparison_docx_report

        return render_comparison_docx_report(output_path=output_path, **kwargs)  # type: ignore[arg-type]

    raise ValueError(f"Unknown format {format!r}. Choose 'html', 'markdown', 'pdf', or 'docx'.")
