"""Bioequivalence report renderers (HTML and Markdown)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from openpkflow import __version__

if TYPE_CHECKING:
    from openpkflow.be.replicate import ReplicateBEResult
    from openpkflow.be.results import BEResult

_DISCLAIMER = (
    "This report was generated using OpenPKFlow -- an open-source Python workflow "
    "for pharmacometric analysis. Final regulatory interpretation should be reviewed "
    "by qualified formulation, pharmacokinetic, and regulatory experts."
)

TEMPLATES_DIR = Path(__file__).parent.parent / "report" / "templates"


def _fmt(v: float) -> str:
    return f"{v:.4g}"


def report_be(result: BEResult, path: str | Path, format: str | None = None) -> None:
    """Write a BE report to *path*.

    Parameters
    ----------
    result : BEResult
        Completed bioequivalence analysis result.
    path : str | Path
        Output file path.
    format : {"html", "markdown", "md"}, optional
        Format override; inferred from extension when None.

    Raises
    ------
    ValueError
        If an unsupported format is requested.
    """
    p = Path(path)
    if format is None:
        ext = p.suffix.lower()
        format = "markdown" if ext in (".md", ".markdown") else "html"

    if format == "markdown":
        _write_markdown(result, p)
    elif format == "html":
        _write_html(result, p)
    else:
        raise ValueError(f"Unsupported format: {format!r}. Use 'html' or 'markdown'.")


def report_replicate_be(
    result: ReplicateBEResult, path: str | Path, format: str | None = None
) -> None:
    """Write a replicate BE report to *path*."""
    p = Path(path)
    if format is None:
        ext = p.suffix.lower()
        format = "markdown" if ext in (".md", ".markdown") else "html"

    if format == "markdown":
        _write_replicate_markdown(result, p)
    elif format == "html":
        _write_replicate_html(result, p)
    else:
        raise ValueError(f"Unsupported format: {format!r}. Use 'html' or 'markdown'.")


def _replicate_summary_rows(result: ReplicateBEResult) -> list[tuple[str, str]]:
    return [
        ("Parameter", result.parameter),
        ("Design", result.design),
        ("Subjects", str(result.n_subjects)),
        ("GMR (T/R)", f"{result.gmr:.4f}"),
        ("90% CI", f"[{result.gmr_lower_90ci:.4f}, {result.gmr_upper_90ci:.4f}]"),
        ("ABE limits", f"[{result.be_lower:.4f}, {result.be_upper:.4f}]"),
        ("ABE conclusion", "PASS" if result.abe_pass else "FAIL"),
        ("CVwR", f"{result.cv_wr_pct:.1f}%"),
        ("Scaled limits", f"[{result.scaled_lower:.4f}, {result.scaled_upper:.4f}]"),
        ("Scaled ABE screen", "PASS" if result.scaled_abe_pass else "FAIL"),
        ("RSABE point screen", "PASS" if result.rsabe_point_pass else "FAIL"),
        ("RSABE criterion", f"{result.rsabe_point_criterion:.6f}"),
    ]


def _write_replicate_markdown(result: ReplicateBEResult, path: Path) -> None:
    lines = [
        "# Replicate Bioequivalence Screening Report",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}  ",
        f"OpenPKFlow v{__version__}",
        "",
        "## Summary",
        "",
        "| Item | Value |",
        "|------|-------|",
    ]
    lines.extend(f"| {label} | {value} |" for label, value in _replicate_summary_rows(result))
    lines += [
        "",
        "## Per-Subject Mean Log Ratios",
        "",
    ]

    cols = list(result.subjects_df.columns)
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for _, row in result.subjects_df.iterrows():
        values = []
        for col in cols:
            value = row[col]
            values.append(f"{value:.6f}" if isinstance(value, float) else str(value))
        lines.append("| " + " | ".join(values) + " |")

    lines += [
        "",
        "## Caveat",
        "",
        result.analysis_note,
        "",
        "---",
        "",
        f"*{_DISCLAIMER}*",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_replicate_html(result: ReplicateBEResult, path: Path) -> None:
    rows = "\n".join(
        f"<tr><th>{label}</th><td>{value}</td></tr>"
        for label, value in _replicate_summary_rows(result)
    )
    cols = list(result.subjects_df.columns)
    header = "".join(f"<th>{col}</th>" for col in cols)
    body_rows = []
    for _, row in result.subjects_df.iterrows():
        cells = []
        for col in cols:
            value = row[col]
            if isinstance(value, float):
                cells.append(f"<td>{value:.6f}</td>")
            else:
                cells.append(f"<td>{value}</td>")
        body_rows.append("<tr>" + "".join(cells) + "</tr>")

    verdict = "PASS" if result.scaled_abe_pass else "FAIL"
    verdict_class = "pass" if result.scaled_abe_pass else "fail"
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Replicate BE Screening Report</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
      color: #1a1a2e; background: #f4f6f9; line-height: 1.6;
    }}
    .page {{
      max-width: 1100px; margin: 32px auto; background: #fff; border-radius: 6px;
      box-shadow: 0 1px 6px rgba(0,0,0,.10); overflow: hidden;
    }}
    header {{ background: #0d3b66; color: #fff; padding: 28px 36px; }}
    main {{ padding: 32px 36px; }}
    h1 {{ margin: 0 0 8px; font-size: 24px; }}
    h2 {{
      color: #0d3b66; font-size: 14px; text-transform: uppercase;
      letter-spacing: .08em; border-bottom: 2px solid #e2ecf8; padding-bottom: 6px;
    }}
    table {{ width: 100%; border-collapse: collapse; margin: 16px 0 28px; }}
    th, td {{ padding: 9px 12px; border-bottom: 1px solid #e8eef6; text-align: left; }}
    th {{ background: #e8f0fb; color: #0d3b66; }}
    .banner {{ padding: 16px 20px; border-radius: 6px; margin-bottom: 24px; font-weight: 700; }}
    .pass {{ background: #e6f9f0; border-left: 6px solid #1a9e6a; color: #0e7a52; }}
    .fail {{ background: #fff0f0; border-left: 6px solid #c0392b; color: #a93226; }}
    .note {{
      background: #f7f9fc; border-left: 3px solid #c6d8f0;
      padding: 12px 16px; font-size: 12px; color: #566;
    }}
    footer {{ color: #777; font-size: 12px; padding: 0 36px 24px; }}
  </style>
</head>
<body>
<div class="page">
  <header>
    <h1>Replicate Bioequivalence Screening Report</h1>
    <div>OpenPKFlow v{__version__} | Generated {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
  </header>
  <main>
    <div class="banner {verdict_class}">Scaled ABE screen: {verdict}</div>
    <h2>Summary</h2>
    <table><tbody>{rows}</tbody></table>
    <h2>Per-Subject Mean Log Ratios</h2>
    <table><thead><tr>{header}</tr></thead><tbody>{"".join(body_rows)}</tbody></table>
    <h2>Caveat</h2>
    <div class="note">{result.analysis_note}</div>
  </main>
  <footer>{_DISCLAIMER}</footer>
</div>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def _write_markdown(result: BEResult, path: Path) -> None:
    verdict = "BIOEQUIVALENT" if result.bioequivalent else "NOT BIOEQUIVALENT"
    lines = [
        "# Bioequivalence Report",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}  ",
        f"OpenPKFlow v{__version__}",
        "",
        "## Summary",
        "",
        "| Item | Value |",
        "|------|-------|",
        f"| Parameter | {result.parameter} |",
        f"| Subjects (n) | {result.n} |",
        f"| GMR (T/R) | {result.gmr:.4f} |",
        f"| 90% CI | [{result.gmr_lower_90ci:.4f}, {result.gmr_upper_90ci:.4f}] |",
        f"| Acceptance limits | [{result.be_lower:.4f}, {result.be_upper:.4f}] |",
        f"| CV (intra) | {result.cv_intra_pct:.1f}% |",
        f"| **Conclusion** | **{verdict}** |",
        "",
        "## Per-Subject Data",
        "",
    ]

    # Header
    cols = list(result.subjects_df.columns)
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for _, row in result.subjects_df.iterrows():
        values = []
        for c in cols:
            v = row[c]
            if isinstance(v, float):
                values.append(f"{v:.4f}")
            else:
                values.append(str(v))
        lines.append("| " + " | ".join(values) + " |")

    lines += ["", "---", "", f"*{_DISCLAIMER}*", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_html(result: BEResult, path: Path) -> None:
    import jinja2

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
    )
    env.globals["zip"] = zip

    template = env.get_template("be_report.html")

    cols = list(result.subjects_df.columns)
    rows = []
    for _, row in result.subjects_df.iterrows():
        cells = {}
        for c in cols:
            v = row[c]
            cells[c] = f"{v:.4f}" if isinstance(v, float) else str(v)
        rows.append(cells)

    verdict = "BIOEQUIVALENT" if result.bioequivalent else "NOT BIOEQUIVALENT"
    verdict_class = "pass" if result.bioequivalent else "fail"

    html = template.render(
        title=f"Bioequivalence Report -- {result.parameter}",
        result=result,
        verdict=verdict,
        verdict_class=verdict_class,
        table_cols=cols,
        table_rows=rows,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        version=__version__,
        disclaimer=_DISCLAIMER,
    )
    path.write_text(html, encoding="utf-8")
