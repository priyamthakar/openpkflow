"""OpenPKFlow CLI - command-line interface built with Typer."""

from __future__ import annotations

from pathlib import Path

import typer

from openpkflow import __version__
from openpkflow.dissolution.loader import DissolutionCSVConfig
from openpkflow.dissolution.similarity import f1, f2
from openpkflow.dissolution.study import DissolutionStudy

app = typer.Typer(
    name="openpkflow",
    help="OpenPKFlow - Python-first pharmacometrics toolkit.",
    add_completion=False,
)

dissolution_app = typer.Typer(help="Dissolution similarity commands.")
app.add_typer(dissolution_app, name="dissolution")


@app.command("version")
def version_command() -> None:
    """Print the installed version of openpkflow."""
    typer.echo(f"openpkflow {__version__}")


@app.command("similarity")
def similarity_command(
    reference: str = typer.Option(
        ...,
        "--reference",
        help="Comma-separated reference dissolution profile (percent released per time point).",
    ),
    test: str = typer.Option(
        ...,
        "--test",
        help="Comma-separated test dissolution profile (percent released per time point).",
    ),
) -> None:
    """Compute f1 and f2 from two comma-separated dissolution profiles.

    Example
    -------
    openpkflow similarity --reference "20,40,60,80,90" --test "21,39,61,79,88"
    """
    try:
        ref_vals = [float(v.strip()) for v in reference.split(",")]
        tst_vals = [float(v.strip()) for v in test.split(",")]
        f1_val = f1(ref_vals, tst_vals)
        f2_val = f2(ref_vals, tst_vals)
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)

    typer.echo(f"f1 = {f1_val:.3f}")
    typer.echo(f"f2 = {f2_val:.2f}")
    interpretation = (
        "f2 >= 50: profiles are similar."
        if f2_val >= 50.0
        else "f2 < 50: profiles are not similar."
    )
    typer.echo(f"Interpretation: {interpretation}")


@dissolution_app.command("compare")
def dissolution_compare(
    csv_path: Path = typer.Argument(
        ...,
        help="Path to dissolution CSV file.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    reference: str = typer.Option(
        ...,
        "--reference",
        help="Label of the reference formulation.",
    ),
    test: str = typer.Option(
        ...,
        "--test",
        help="Label of the test formulation.",
    ),
    formulation_col: str = typer.Option("formulation", help="Formulation column name."),
    batch_col: str = typer.Option("batch", help="Batch column name."),
    time_col: str = typer.Option("time", help="Time column name."),
    percent_released_col: str = typer.Option(
        "percent_released", help="Percent released column name."
    ),
    report: Path | None = typer.Option(
        None,
        "--report",
        help="Write an HTML or Markdown report to this path (format inferred from extension).",
    ),
) -> None:
    """Compare two formulations in a dissolution CSV using f1 and f2."""
    config = DissolutionCSVConfig(
        formulation_col=formulation_col,
        batch_col=batch_col,
        time_col=time_col,
        percent_released_col=percent_released_col,
    )
    try:
        study = DissolutionStudy.from_csv(csv_path, config)
        result = study.compare(reference, test)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)

    typer.echo(result.summary())

    if report is not None:
        _rp = str(report)
        if _rp.endswith((".md", ".markdown")):
            fmt = "markdown"
        elif _rp.endswith(".pdf"):
            fmt = "pdf"
        elif _rp.endswith(".docx"):
            fmt = "docx"
        else:
            fmt = "html"
        try:
            result.report(report, format=fmt)
            typer.echo(f"\nReport written to: {report}")
        except Exception as exc:  # noqa: BLE001
            typer.echo(f"Warning: could not write report: {exc}", err=True)
