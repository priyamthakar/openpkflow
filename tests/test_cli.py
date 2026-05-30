"""CLI tests for openpkflow using typer.testing.CliRunner."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

from typer.testing import CliRunner

from openpkflow.cli import app

runner = CliRunner()


def test_version() -> None:
    """openpkflow version prints the package version string."""
    from openpkflow import __version__

    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_similarity_command() -> None:
    """Identical profiles yield f2 = 100 and f1 = 0.

    Reference: FDA 1997 guidance — f2 = 100 by definition when R == T.
    """
    result = runner.invoke(
        app,
        [
            "similarity",
            "--reference",
            "20,40,60,80,90",
            "--test",
            "20,40,60,80,90",
        ],
    )
    assert result.exit_code == 0
    assert "100" in result.output


def test_similarity_similar_profiles() -> None:
    """Profiles that differ slightly should produce f2 >= 50 (similar).

    Reference: FDA 1997 guidance — f2 >= 50 indicates similarity.
    """
    result = runner.invoke(
        app,
        [
            "similarity",
            "--reference",
            "20,40,60,80,90",
            "--test",
            "21,39,61,79,88",
        ],
    )
    assert result.exit_code == 0
    assert "f1" in result.output
    assert "f2" in result.output
    assert "similar" in result.output.lower()


def test_similarity_invalid_input() -> None:
    """Mismatched profile lengths must cause exit code 1."""
    result = runner.invoke(
        app,
        [
            "similarity",
            "--reference",
            "20,40",
            "--test",
            "20,40,60",
        ],
    )
    assert result.exit_code == 1


def test_similarity_non_numeric_input() -> None:
    """Non-numeric values in profiles must cause exit code 1."""
    result = runner.invoke(
        app,
        [
            "similarity",
            "--reference",
            "20,abc,60",
            "--test",
            "20,40,60",
        ],
    )
    assert result.exit_code == 1


SAMPLE_CSV = textwrap.dedent("""\
    formulation,batch,time,percent_released
    reference,R1,5,18.2
    reference,R1,10,31.4
    reference,R1,15,47.9
    reference,R1,30,65.0
    test,T1,5,17.5
    test,T1,10,30.1
    test,T1,15,46.2
    test,T1,30,63.8
""")


def test_dissolution_compare(tmp_path: Path) -> None:
    """dissolution compare prints a summary with f1 and f2.

    Uses a minimal CSV with reference and test formulations across 4 time points
    (minimum 3 required by FDA guidance).
    """
    csv_file = tmp_path / "dissolution.csv"
    csv_file.write_text(SAMPLE_CSV)

    result = runner.invoke(
        app,
        [
            "dissolution",
            "compare",
            str(csv_file),
            "--reference",
            "reference",
            "--test",
            "test",
        ],
    )
    assert result.exit_code == 0
    assert "f1" in result.output
    assert "f2" in result.output
    assert "reference" in result.output
    assert "test" in result.output


def test_dissolution_compare_missing_formulation(tmp_path: Path) -> None:
    """dissolution compare exits 1 when the requested formulation is not in the CSV."""
    csv_file = tmp_path / "dissolution.csv"
    csv_file.write_text(SAMPLE_CSV)

    result = runner.invoke(
        app,
        [
            "dissolution",
            "compare",
            str(csv_file),
            "--reference",
            "reference",
            "--test",
            "placebo",
        ],
    )
    assert result.exit_code == 1


def test_dissolution_compare_missing_file() -> None:
    """dissolution compare exits 1 when the CSV file does not exist.

    Note: typer validates the Argument path itself and may produce exit code 2
    for a missing file before our handler runs.
    """
    result = runner.invoke(
        app,
        [
            "dissolution",
            "compare",
            "nonexistent_file.csv",
            "--reference",
            "reference",
            "--test",
            "test",
        ],
    )
    assert result.exit_code != 0


def test_dissolution_compare_mismatched_timepoints(tmp_path: Path) -> None:
    """dissolution compare exits 1 when reference and test have different time points."""
    mismatched_csv = textwrap.dedent("""\
        formulation,batch,time,percent_released
        reference,R1,5,18.2
        reference,R1,10,31.4
        reference,R1,15,47.9
        reference,R1,30,65.0
        test,T1,5,17.5
        test,T1,10,30.1
        test,T1,20,46.2
        test,T1,30,63.8
    """)
    csv_file = tmp_path / "mismatched.csv"
    csv_file.write_text(mismatched_csv)

    result = runner.invoke(
        app,
        [
            "dissolution",
            "compare",
            str(csv_file),
            "--reference",
            "reference",
            "--test",
            "test",
        ],
    )
    assert result.exit_code == 1


REPLICATE_BE_CSV = textwrap.dedent("""\
    subject,sequence,period,treatment,Cmax
    S01,TRR,1,T,105.0
    S01,TRR,2,R,92.0
    S01,TRR,3,R,108.0
    S02,RTR,1,R,95.0
    S02,RTR,2,T,101.0
    S02,RTR,3,R,110.0
    S03,RRT,1,R,91.0
    S03,RRT,2,R,106.0
    S03,RRT,3,T,100.0
""")


def test_be_replicate_cli_prints_summary(tmp_path: Path) -> None:
    csv_file = tmp_path / "replicate.csv"
    csv_file.write_text(REPLICATE_BE_CSV)

    result = runner.invoke(app, ["be", "replicate", str(csv_file), "--parameter", "Cmax"])

    assert result.exit_code == 0
    assert "Replicate BE Summary" in result.output
    assert "Cmax" in result.output
    assert "GMR" in result.output
    assert "CVwR" in result.output


def test_be_replicate_cli_writes_html_and_json(tmp_path: Path) -> None:
    csv_file = tmp_path / "replicate.csv"
    html_file = tmp_path / "replicate.html"
    json_file = tmp_path / "replicate.json"
    csv_file.write_text(REPLICATE_BE_CSV)

    result = runner.invoke(
        app,
        [
            "be",
            "replicate",
            str(csv_file),
            "--parameter",
            "Cmax",
            "--report",
            str(html_file),
            "--json",
            str(json_file),
        ],
    )

    assert result.exit_code == 0
    assert html_file.exists()
    assert json_file.exists()
    assert "Replicate" in html_file.read_text(encoding="utf-8")
    assert "Cmax" in html_file.read_text(encoding="utf-8")
    payload = json.loads(json_file.read_text(encoding="utf-8"))
    assert payload["parameter"] == "Cmax"
    assert "gmr" in payload
    assert "cv_wr_pct" in payload
    assert "scaled_lower" in payload
    assert "subjects" in payload


def test_be_replicate_cli_missing_parameter_exits_1(tmp_path: Path) -> None:
    csv_file = tmp_path / "replicate.csv"
    csv_file.write_text(REPLICATE_BE_CSV)

    result = runner.invoke(app, ["be", "replicate", str(csv_file), "--parameter", "AUCinf"])

    assert result.exit_code == 1
    assert "AUCinf" in result.output
