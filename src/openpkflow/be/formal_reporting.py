"""Formal crossover ANOVA report renderers."""

from __future__ import annotations

from pathlib import Path

from openpkflow import __version__
from openpkflow.be.formal import FormalBEResult

_DISCLAIMER = (
    "This report was generated using OpenPKFlow (open-source). Final regulatory "
    "interpretation should be reviewed by qualified formulation, pharmacokinetic, "
    "and regulatory experts."
)


def report_formal_be(result: FormalBEResult, path: str | Path, format: str | None = None) -> None:
    """Write a formal ANOVA report as HTML or Markdown."""
    output = Path(path)
    selected = format or ("markdown" if output.suffix.lower() in {".md", ".markdown"} else "html")
    if selected == "markdown":
        output.write_text(_markdown(result), encoding="utf-8")
    elif selected == "html":
        output.write_text(_html(result), encoding="utf-8")
    else:
        raise ValueError("Unsupported format. Use 'html' or 'markdown'.")


def _markdown(result: FormalBEResult) -> str:
    ci_label = f"{result.confidence_level_pct:g}% CI"
    lines = [
        "# Formal 2x2 Crossover Bioequivalence ANOVA",
        "",
        f"OpenPKFlow v{__version__}",
        "",
        "## Treatment Contrast",
        "",
        "| Item | Value |",
        "|---|---|",
        f"| Parameter | {result.parameter} |",
        f"| Subjects | {result.n_subjects} |",
        f"| GMR (T/R) | {result.gmr:.6f} |",
        f"| {ci_label} | [{result.gmr_lower_ci:.6f}, {result.gmr_upper_ci:.6f}] |",
        f"| Acceptance limits | [{result.be_lower:.4f}, {result.be_upper:.4f}] |",
        f"| Residual MSE | {result.residual_mse:.8f} |",
        f"| Intra-subject CV | {result.cv_intra_pct:.3f}% |",
        f"| Decision | {result.decision} |",
        "",
        "## ANOVA Table",
        "",
        "| Source | DF | SS | MS | F | p-value |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in result.anova:
        lines.append(
            f"| {row.source} | {row.df} | {row.sum_squares:.8f} | "
            f"{'' if row.mean_square is None else f'{row.mean_square:.8f}'} | "
            f"{'' if row.f_value is None else f'{row.f_value:.6f}'} | "
            f"{'' if row.p_value is None else f'{row.p_value:.6g}'} |"
        )
    lines += ["", "---", "", f"*{_DISCLAIMER}*", ""]
    return "\n".join(lines)


def _html(result: FormalBEResult) -> str:
    import html

    ci_label = f"{result.confidence_level_pct:g}% CI"
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(row.source)}</td><td>{row.df}</td><td>{row.sum_squares:.8f}</td>"
        f"<td>{'' if row.mean_square is None else f'{row.mean_square:.8f}'}</td>"
        f"<td>{'' if row.f_value is None else f'{row.f_value:.6f}'}</td>"
        f"<td>{'' if row.p_value is None else f'{row.p_value:.6g}'}</td>"
        "</tr>"
        for row in result.anova
    )
    decision_class = "pass" if result.decision == "PASS" else "fail"
    summary_rows = "".join(
        [
            f"<tr><th>Parameter</th><td>{html.escape(result.parameter)}</td></tr>",
            f"<tr><th>Subjects</th><td>{result.n_subjects}</td></tr>",
            f"<tr><th>GMR (T/R)</th><td>{result.gmr:.6f}</td></tr>",
            f"<tr><th>{ci_label}</th><td>[{result.gmr_lower_ci:.6f}, "
            f"{result.gmr_upper_ci:.6f}]</td></tr>",
            f"<tr><th>Limits</th><td>[{result.be_lower:.4f}, {result.be_upper:.4f}]</td></tr>",
            f"<tr><th>Residual MSE</th><td>{result.residual_mse:.8f}</td></tr>",
            f"<tr><th>Intra-subject CV</th><td>{result.cv_intra_pct:.3f}%</td></tr>",
        ]
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Formal BE ANOVA</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 2rem; color: #172033; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #cbd5e1; padding: .5rem; text-align: left; }}
th {{ background: #e2e8f0; }} .pass {{ color: #166534; }} .fail {{ color: #b91c1c; }}
</style></head><body>
<h1>Formal 2x2 Crossover Bioequivalence ANOVA</h1><p>OpenPKFlow v{__version__}</p>
<h2>Decision</h2><p class="{decision_class}"><strong>{result.decision}</strong></p>
<table>{summary_rows}</table>
<h2>ANOVA Table</h2>
<table><thead><tr><th>Source</th><th>DF</th><th>SS</th><th>MS</th><th>F</th><th>p-value</th></tr></thead><tbody>{rows}</tbody></table>
<footer>{html.escape(_DISCLAIMER)}</footer></body></html>"""
