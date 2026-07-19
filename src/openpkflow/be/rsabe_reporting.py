"""FDA partial-replicate RSABE report renderers."""

from __future__ import annotations

from pathlib import Path

from openpkflow import __version__
from openpkflow.be.rsabe import FdaRsabeResult

_DISCLAIMER = (
    "This report was generated using OpenPKFlow (open-source). Final regulatory "
    "interpretation should be reviewed by qualified formulation, pharmacokinetic, "
    "and regulatory experts."
)


def report_rsabe(result: FdaRsabeResult, path: str | Path, format: str | None = None) -> None:
    """Write an FDA partial-replicate RSABE report as HTML or Markdown."""
    output = Path(path)
    selected = format or ("markdown" if output.suffix.lower() in {".md", ".markdown"} else "html")
    if selected == "markdown":
        output.write_text(_markdown(result), encoding="utf-8")
    elif selected == "html":
        output.write_text(_html(result), encoding="utf-8")
    else:
        raise ValueError("Unsupported format. Use 'html' or 'markdown'.")


def _rows(result: FdaRsabeResult) -> list[tuple[str, str]]:
    ci_label = f"{result.confidence_level_pct:g}% CI"
    return [
        ("Parameter", result.parameter),
        ("Design", result.design),
        ("Subjects", str(result.n_subjects)),
        ("GMR (T/R)", f"{result.gmr:.6f}"),
        (f"GMR {ci_label}", f"[{result.gmr_ci_lower:.6f}, {result.gmr_ci_upper:.6f}]"),
        ("Reference intra-subject CV", f"{result.cv_wr_pct:.3f}%"),
        ("Highly variable (CVwR >= 30%)", "Yes" if result.highly_variable else "No"),
        ("Theta (regulatory constant)", f"{result.theta:.6f}"),
        ("Aggregate criterion (point)", f"{result.aggregate_criterion_point:.6f}"),
        ("Aggregate criterion (95% upper bound)", f"{result.aggregate_criterion_upper:.6f}"),
        (
            "Point estimate constraint (0.80, 1.25)",
            "Met" if result.point_estimate_constraint_met else "Not met",
        ),
    ]


def _markdown(result: FdaRsabeResult) -> str:
    lines = [
        "# FDA Partial-Replicate RSABE",
        "",
        f"OpenPKFlow v{__version__}",
        "",
        "## Result",
        "",
        "| Item | Value |",
        "|---|---|",
    ]
    lines += [f"| {label} | {value} |" for label, value in _rows(result)]
    lines += [
        f"| Decision | {result.decision} |",
        "",
        result.message,
        "",
        "---",
        "",
        f"*{_DISCLAIMER}*",
        "",
    ]
    return "\n".join(lines)


def _html(result: FdaRsabeResult) -> str:
    import html

    rows = "".join(
        f"<tr><th>{html.escape(label)}</th><td>{html.escape(value)}</td></tr>"
        for label, value in _rows(result)
    )
    decision_class = {"PASS": "pass", "FAIL": "fail"}.get(result.decision, "not-evaluable")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>FDA Partial-Replicate RSABE</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 2rem; color: #172033; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #cbd5e1; padding: .5rem; text-align: left; }}
th {{ background: #e2e8f0; }} .pass {{ color: #166534; }} .fail {{ color: #b91c1c; }}
.not-evaluable {{ color: #92400e; }}
</style></head><body>
<h1>FDA Partial-Replicate RSABE</h1><p>OpenPKFlow v{__version__}</p>
<h2>Decision</h2><p class="{decision_class}"><strong>{html.escape(result.decision)}</strong></p>
<p>{html.escape(result.message)}</p>
<table>{rows}</table>
<footer>{html.escape(_DISCLAIMER)}</footer></body></html>"""
