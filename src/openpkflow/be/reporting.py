"""Bioequivalence report renderers (HTML and Markdown)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from openpkflow import __version__

if TYPE_CHECKING:
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
