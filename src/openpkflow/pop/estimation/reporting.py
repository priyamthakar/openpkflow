"""Population PK estimation reporting — HTML and Markdown."""

from __future__ import annotations

from pathlib import Path

from .plotting import pop_pk_plot_b64
from .result import PopPKResult


def report_pop_pk(
    result: PopPKResult,
    *,
    output_path: str | Path,
    fmt: str = "html",
) -> str:
    """Generate a population PK estimation report.

    Parameters
    ----------
    result : PopPKResult
        Estimation result.
    output_path : str or Path
        Path for the output file.
    fmt : str
        ``"html"`` or ``"markdown"``.

    Returns
    -------
    str
        Report content as a string.

    Raises
    ------
    ValueError
        If format is unsupported.
    """
    out = Path(output_path)
    if fmt == "html":
        content = _pop_pk_html(result)
        out.write_text(content, encoding="utf-8")
        return content
    elif fmt == "markdown":
        content = _pop_pk_markdown(result)
        out.write_text(content, encoding="utf-8")
        return content
    else:
        raise ValueError(f"Unsupported report format: {fmt}")


def _pop_pk_html(result: PopPKResult) -> str:
    plot_b64 = pop_pk_plot_b64(result)

    param_rows = _build_param_rows(result)
    param_table = _build_html_table(["Parameter", "Estimate", "SE", "RSE%"], param_rows)

    omega_rows = _build_omega_rows(result)
    omega_table = _build_html_table(["Parameter", "Omega", "SE", "RSE%"], omega_rows)

    sigma_rows = [
        ["sigma_prop", f"{result.sigma_prop:.4f}", f"{result.sigma_prop_se:.4f}", "N/A"],
        ["sigma_add", f"{result.sigma_add:.4f}", f"{result.sigma_add_se:.4f}", "N/A"],
    ]
    sigma_table = _build_html_table(["Parameter", "Estimate", "SE", "RSE%"], sigma_rows)

    shrinkage_rows = [[k, f"{v:.1%}", "", ""] for k, v in result.shrinkage.items()]
    shrinkage_table = _build_html_table(["Parameter", "Shrinkage", "", ""], shrinkage_rows)

    warnings_html = ""
    if result.warnings:
        warnings_html = (
            "<h3>Warnings</h3>\n<ul>\n"
            + "\n".join(f"  <li>{w}</li>" for w in result.warnings)
            + "\n</ul>\n"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Population PK Estimation — {result.method}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 900px; margin: 2em auto; padding: 0 1em; color: #222; }}
h1 {{ border-bottom: 2px solid #0366d6; padding-bottom: 0.3em; }}
h2 {{ margin-top: 1.5em; }}
table {{ border-collapse: collapse; width: 100%; margin: 0.5em 0 1.5em; }}
th, td {{ text-align: left; padding: 6px 12px; border-bottom: 1px solid #ddd; }}
th {{ background: #f6f8fa; font-weight: 600; }}
tr:nth-child(even) {{ background: #fafbfc; }}
.disclaimer {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 1em; margin: 2em 0; font-size: 0.9em; }}
.warnings {{ background: #fff3cd; border-left: 4px solid #dc3545; padding: 1em; margin: 1em 0; }}
img {{ max-width: 100%; height: auto; }}
</style>
</head>
<body>

<h1>Population PK Estimation — {result.method}</h1>

<p><strong>Study:</strong> {result.study_label or "N/A"} &nbsp;|&nbsp;
<strong>Route:</strong> {result.route} &nbsp;|&nbsp;
<strong>Subjects:</strong> {result.n_subjects} &nbsp;|&nbsp;
<strong>Observations:</strong> {result.n_observations}</p>

<h2>Model Fit</h2>
<table>
<tr><th>Metric</th><th>Value</th></tr>
<tr><td>-2LL</td><td>{result.minus2ll:.1f}</td></tr>
<tr><td>AIC</td><td>{result.aic:.1f}</td></tr>
<tr><td>BIC</td><td>{result.bic:.1f}</td></tr>
<tr><td>Converged</td><td>{result.converged}</td></tr>
<tr><td>Uncertainty reliable</td><td>{result.uncertainty_reliable}</td></tr>
<tr><td>Gradient norm</td><td>{result.gradient_norm:.2e}</td></tr>
<tr><td>Condition number</td><td>{result.condition_number:.1f}</td></tr>
<tr><td>EBE failures</td><td>{result.n_inner_failures}/{result.n_subjects}</td></tr>
<tr><td>Iterations</td><td>{result.iterations}</td></tr>
<tr><td>Elapsed time</td><td>{result.elapsed_time:.1f}s</td></tr>
</table>

<h2>Fixed Effects (Population Typical Values)</h2>
{param_table}

<h2>Between-Subject Variability (Omega diagonal)</h2>
{omega_table}

<h2>Residual Error</h2>
{sigma_table}

<h2>EBE Shrinkage</h2>
{shrinkage_table}

<h2>Diagnostic Plot</h2>
<img src="data:image/png;base64,{plot_b64}" alt="Population PK diagnostic plot">

{warnings_html}

<div class="disclaimer">
<strong>Disclaimer:</strong> This is a research tool. Results should be verified
against a regulatory-grade population PK engine (NONMEM, Monolix, nlmixr2).
Population PK estimates are for exploratory analysis and simulation only and
should not form the sole basis of regulatory decisions.
</div>

</body>
</html>"""


def _pop_pk_markdown(result: PopPKResult) -> str:
    lines: list[str] = []
    lines.append(f"# Population PK Estimation — {result.method}")
    lines.append("")
    lines.append(f"- **Study:** {result.study_label or 'N/A'}")
    lines.append(f"- **Route:** {result.route}")
    lines.append(f"- **Subjects:** {result.n_subjects}")
    lines.append(f"- **Observations:** {result.n_observations}")
    lines.append("")

    lines.append("## Model Fit")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| -2LL | {result.minus2ll:.1f} |")
    lines.append(f"| AIC | {result.aic:.1f} |")
    lines.append(f"| BIC | {result.bic:.1f} |")
    lines.append(f"| Converged | {result.converged} |")
    lines.append(f"| Uncertainty reliable | {result.uncertainty_reliable} |")
    lines.append(f"| Gradient norm | {result.gradient_norm:.2e} |")
    lines.append(f"| Condition number | {result.condition_number:.1f} |")
    lines.append(f"| EBE failures | {result.n_inner_failures}/{result.n_subjects} |")
    lines.append(f"| Iterations | {result.iterations} |")
    lines.append(f"| Elapsed time | {result.elapsed_time:.1f}s |")
    lines.append("")

    lines.append("## Fixed Effects")
    lines.append("")
    lines.append("| Parameter | Estimate | SE | RSE% |")
    lines.append("|-----------|----------|----|------|")
    for k in result.param_names:
        lines.append(
            f"| {k} | {result.theta_pop.get(k, float('nan')):.4f} "
            f"| {result.theta_se.get(k, float('nan')):.4f} "
            f"| {result.rse.get(k, float('nan')):.1f} |"
        )
    lines.append("")

    lines.append("## Between-Subject Variability")
    lines.append("")
    lines.append("| Parameter | Omega | SE | RSE% |")
    lines.append("|-----------|-------|----|------|")
    for k in result.param_names:
        omega_rse = (
            100.0 * result.omega_se.get(k, 0) / result.omega_diag.get(k, 1)
            if result.omega_diag.get(k, 0) > 0
            else float("nan")
        )
        lines.append(
            f"| omega_{k} | {result.omega_diag.get(k, float('nan')):.4f} "
            f"| {result.omega_se.get(k, float('nan')):.4f} "
            f"| {omega_rse:.1f} |"
        )
    lines.append("")

    lines.append("## Residual Error")
    lines.append("")
    lines.append(f"- sigma_prop = {result.sigma_prop:.4f} (SE = {result.sigma_prop_se:.4f})")
    lines.append(f"- sigma_add  = {result.sigma_add:.4f} (SE = {result.sigma_add_se:.4f})")
    lines.append("")

    lines.append("## EBE Shrinkage")
    lines.append("")
    for k, v in result.shrinkage.items():
        lines.append(f"- {k}: {v:.1%}")
    lines.append("")

    if result.warnings:
        lines.append("## Warnings")
        lines.append("")
        for w in result.warnings:
            lines.append(f"- {w}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        "*Disclaimer: This is a research tool. Results should be verified against "
        "a regulatory-grade population PK engine (NONMEM, Monolix, nlmixr2).*"
    )

    return "\n".join(lines)


def _build_param_rows(result: PopPKResult) -> list[list[str]]:
    rows: list[list[str]] = []
    for k in result.param_names:
        rows.append(
            [
                k,
                f"{result.theta_pop.get(k, float('nan')):.4f}",
                f"{result.theta_se.get(k, float('nan')):.4f}",
                f"{result.rse.get(k, float('nan')):.1f}",
            ]
        )
    return rows


def _build_omega_rows(result: PopPKResult) -> list[list[str]]:
    rows: list[list[str]] = []
    for k in result.param_names:
        omega_rse = (
            100.0 * result.omega_se.get(k, 0) / result.omega_diag.get(k, 1)
            if result.omega_diag.get(k, 0) > 0
            else float("nan")
        )
        rows.append(
            [
                f"omega_{k}",
                f"{result.omega_diag.get(k, float('nan')):.4f}",
                f"{result.omega_se.get(k, float('nan')):.4f}",
                f"{omega_rse:.1f}",
            ]
        )
    return rows


def _build_html_table(headers: list[str], rows: list[list[str]]) -> str:
    thead = "".join(f"<th>{h}</th>" for h in headers)
    tbody = "\n".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows)
    return f"<table>\n<thead><tr>{thead}</tr></thead>\n<tbody>\n{tbody}\n</tbody>\n</table>"
