"""Integration tests for DissolutionStudy, loader, and report generation."""

from __future__ import annotations

import warnings
from pathlib import Path

import pytest

from openpkflow.datasets import example_dissolution_path as _example_path
from openpkflow.dissolution import DissolutionStudy  # noqa: E402
from openpkflow.dissolution.loader import load_dissolution_csv  # noqa: E402
from openpkflow.dissolution.reporting import render_markdown_report  # noqa: E402
from openpkflow.report.html import render_html_report  # noqa: E402

EXAMPLE_DISSOLUTION_CSV = _example_path()

# ---------------------------------------------------------------------------
# Loader tests
# ---------------------------------------------------------------------------


def test_load_example_csv_shape() -> None:
    """Example CSV loads into a DataFrame with expected shape."""
    df = load_dissolution_csv(EXAMPLE_DISSOLUTION_CSV)
    assert df.shape[0] == 36  # 2 formulations × 3 batches × 6 timepoints
    assert set(df.columns) == {"formulation", "batch", "time", "percent_released"}


def test_load_example_csv_formulations() -> None:
    """Example CSV contains exactly two formulations: reference and test."""
    df = load_dissolution_csv(EXAMPLE_DISSOLUTION_CSV)
    assert set(df["formulation"].unique()) == {"reference", "test"}


def test_load_missing_file_raises() -> None:
    """FileNotFoundError is raised for a non-existent CSV path."""
    with pytest.raises(FileNotFoundError):
        load_dissolution_csv("non_existent_file.csv")


def test_load_missing_columns_raises(tmp_path: Path) -> None:
    """ValueError is raised when required columns are missing."""
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("time,value\n5,10\n10,20\n")
    with pytest.raises(ValueError, match="missing"):
        load_dissolution_csv(bad_csv)


def test_load_out_of_range_values_raises(tmp_path: Path) -> None:
    """ValueError is raised when percent_released exceeds 100."""
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text(
        "formulation,batch,time,percent_released\nreference,R1,5,110\n"
    )
    with pytest.raises(ValueError, match="outside"):
        load_dissolution_csv(bad_csv)


# ---------------------------------------------------------------------------
# DissolutionStudy tests
# ---------------------------------------------------------------------------


def test_study_from_csv_loads() -> None:
    """DissolutionStudy.from_csv loads the example dataset without error."""
    study = DissolutionStudy.from_csv(EXAMPLE_DISSOLUTION_CSV)
    assert "reference" in study.formulations()
    assert "test" in study.formulations()


def test_study_compare_returns_result() -> None:
    """DissolutionStudy.compare returns a ComparisonResult with valid f1/f2."""
    study = DissolutionStudy.from_csv(EXAMPLE_DISSOLUTION_CSV)
    result = study.compare(reference="reference", test="test")
    assert 0.0 <= result.f1_value <= 100.0
    assert 0.0 <= result.f2_value <= 100.0
    assert result.n_timepoints == 6


def test_study_compare_f2_range() -> None:
    """f2 for the example dataset is between 50 and 70 (profiles are similar but not identical)."""
    study = DissolutionStudy.from_csv(EXAMPLE_DISSOLUTION_CSV)
    result = study.compare(reference="reference", test="test")
    assert 50.0 <= result.f2_value <= 70.0, (
        f"Expected f2 between 50 and 70 for the example dataset; got {result.f2_value:.2f}"
    )


def test_study_compare_unknown_formulation_raises() -> None:
    """ValueError is raised when a formulation label is not in the dataset."""
    study = DissolutionStudy.from_csv(EXAMPLE_DISSOLUTION_CSV)
    with pytest.raises(ValueError, match="not found"):
        study.compare(reference="reference", test="nonexistent")


def test_study_compare_summary_contains_f2() -> None:
    """ComparisonResult.summary() includes f2 value and interpretation text."""
    study = DissolutionStudy.from_csv(EXAMPLE_DISSOLUTION_CSV)
    result = study.compare(reference="reference", test="test")
    summary = result.summary()
    assert "f2" in summary
    assert "Disclaimer" in summary


def test_study_compare_to_dict() -> None:
    """ComparisonResult.to_dict() returns all expected keys."""
    study = DissolutionStudy.from_csv(EXAMPLE_DISSOLUTION_CSV)
    result = study.compare(reference="reference", test="test")
    d = result.to_dict()
    assert set(d.keys()) == {
        "reference_label", "test_label", "f1_value", "f2_value",
        "n_timepoints", "reference_mean", "test_mean", "time_points",
    }


def test_study_compare_85pct_warning(tmp_path: Path) -> None:
    """UserWarning is emitted when more than one mean exceeds 85%."""
    csv = tmp_path / "high.csv"
    csv.write_text(
        "formulation,batch,time,percent_released\n"
        "ref,R1,5,20\nref,R1,15,60\nref,R1,30,88\nref,R1,45,92\nref,R1,60,96\n"
        "tst,T1,5,19\ntst,T1,15,58\ntst,T1,30,86\ntst,T1,45,90\ntst,T1,60,94\n"
    )
    study = DissolutionStudy.from_csv(csv)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        study.compare(reference="ref", test="tst")
    assert any("85%" in str(w.message) for w in caught), (
        "Expected a UserWarning about the >85% timepoint rule"
    )


# ---------------------------------------------------------------------------
# Report generation tests
# ---------------------------------------------------------------------------


def test_markdown_report_roundtrip(tmp_path: Path) -> None:
    """render_markdown_report writes a file and returns the same string."""
    out = tmp_path / "report.md"
    study = DissolutionStudy.from_csv(EXAMPLE_DISSOLUTION_CSV)
    result = study.compare(reference="reference", test="test")
    rendered = render_markdown_report(
        title="Test Report",
        reference_label=result.reference_label,
        test_label=result.test_label,
        f1_value=result.f1_value,
        f2_value=result.f2_value,
        n_timepoints=result.n_timepoints,
        time_points=result.time_points,
        reference_mean=result.reference_mean,
        test_mean=result.test_mean,
        output_path=out,
    )
    assert out.exists()
    assert out.read_text(encoding="utf-8") == rendered
    assert "f2" in rendered
    assert "Disclaimer" in rendered


def test_html_report_roundtrip(tmp_path: Path) -> None:
    """render_html_report writes a file and returns valid HTML."""
    out = tmp_path / "report.html"
    study = DissolutionStudy.from_csv(EXAMPLE_DISSOLUTION_CSV)
    result = study.compare(reference="reference", test="test")
    rendered = render_html_report(
        title="Test HTML Report",
        reference_label=result.reference_label,
        test_label=result.test_label,
        f1_value=result.f1_value,
        f2_value=result.f2_value,
        n_timepoints=result.n_timepoints,
        time_points=result.time_points,
        reference_mean=result.reference_mean,
        test_mean=result.test_mean,
        output_path=out,
    )
    assert out.exists()
    assert "<!DOCTYPE html>" in rendered
    assert "OpenPKFlow" in rendered
    assert "Disclaimer" in rendered


def test_comparison_result_report_html(tmp_path: Path) -> None:
    """ComparisonResult.report() writes an HTML file via the convenience method."""
    out = tmp_path / "dissolution_report.html"
    study = DissolutionStudy.from_csv(EXAMPLE_DISSOLUTION_CSV)
    result = study.compare(reference="reference", test="test")
    rendered = result.report(out, format="html")
    assert out.exists()
    assert "<!DOCTYPE html>" in rendered


def test_comparison_result_report_markdown(tmp_path: Path) -> None:
    """ComparisonResult.report() writes a Markdown file via the convenience method."""
    out = tmp_path / "dissolution_report.md"
    study = DissolutionStudy.from_csv(EXAMPLE_DISSOLUTION_CSV)
    result = study.compare(reference="reference", test="test")
    rendered = result.report(out, format="markdown")
    assert out.exists()
    assert "# " in rendered


# ---------------------------------------------------------------------------
# CV warning tests
# ---------------------------------------------------------------------------


class TestCVWarning:
    def test_high_cv_early_timepoint_warns(self, tmp_path):
        # CV > 20% at t=5 min (early timepoint)
        csv = tmp_path / "high_cv.csv"
        csv.write_text(
            "formulation,batch,time,percent_released\n"
            "reference,R1,5,10.0\n"
            "reference,R2,5,50.0\n"  # huge spread -> CV >> 20%
            "reference,R1,15,60.0\n"
            "reference,R2,15,62.0\n"
            "reference,R1,30,80.0\n"
            "reference,R2,30,81.0\n"
            "test,T1,5,11.0\n"
            "test,T2,5,51.0\n"
            "test,T1,15,61.0\n"
            "test,T2,15,63.0\n"
            "test,T1,30,79.0\n"
            "test,T2,30,80.0\n"
        )
        study = DissolutionStudy.from_csv(str(csv))
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            study.compare("reference", "test")
            cv_warns = [x for x in w if "CV" in str(x.message)]
            assert len(cv_warns) >= 1
            assert "CV" in str(cv_warns[0].message)

    def test_low_cv_no_warning(self):
        from openpkflow.datasets import example_dissolution_path
        study = DissolutionStudy.from_csv(example_dissolution_path())
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            study.compare("reference", "test")
            cv_warns = [x for x in w if "CV" in str(x.message)]
            assert len(cv_warns) == 0
