from __future__ import annotations

from pathlib import Path

from openpkflow import __version__

_DISCLAIMER = (
    "This report was generated using OpenPKFlow — an open-source Python workflow "
    "for pharmacometric analysis. Final regulatory interpretation should be reviewed "
    "by qualified formulation, pharmacokinetic, and regulatory experts."
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
    """Render a dissolution comparison Markdown report."""
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

    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"**Generated:** {generated_at}  ")
    lines.append(f"**OpenPKFlow version:** {__version__}")
    lines.append("")

    lines.append("## Study Parameters")
    lines.append("")
    lines.append("| Parameter | Value |")
    lines.append("|-----------|-------|")
    lines.append(f"| Reference | {reference_label} |")
    lines.append(f"| Test | {test_label} |")
    lines.append(f"| Timepoints (n) | {n_timepoints} |")
    lines.append("")

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

    lines.append("## Dissolution Profile Data")
    lines.append("")
    lines.append(
        f"| Time (min) | {reference_label} Mean (%) | {test_label} Mean (%) | Difference (%) |"
    )
    lines.append("|----------:|------------------:|---------------:|---------------:|")
    for t, r, ts in zip(time_points, reference_mean, test_mean, strict=True):
        lines.append(f"| {t} | {r:.2f} | {ts:.2f} | {ts - r:.2f} |")
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


def report_dissolution(
    *,
    output_path: str | Path,
    format: str = "html",
    **kwargs: object,
) -> str | bytes:
    """Generate a dissolution comparison report in the specified format."""
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


def report_multi_media(
    *,
    output_path: str | Path,
    format: str = "html",
    **kwargs: object,
) -> str | bytes:
    """Generate a multi-media dissolution report in the specified format."""
    if format == "html":
        from openpkflow.report.html import render_multi_media_html_report

        return render_multi_media_html_report(output_path=output_path, **kwargs)  # type: ignore[arg-type]

    if format == "pdf":
        from openpkflow.report.pdf import render_multi_media_pdf_report

        return render_multi_media_pdf_report(output_path=output_path, **kwargs)  # type: ignore[arg-type]

    if format == "docx":
        from openpkflow.report.docx import render_multi_media_docx_report

        return render_multi_media_docx_report(output_path=output_path, **kwargs)  # type: ignore[arg-type]

    raise ValueError(f"Unknown format {format!r}. Choose 'html', 'pdf', or 'docx'.")
