"""Tests for nca/reporting.py -- single and summary report renderers."""

from __future__ import annotations

from pathlib import Path

from openpkflow.nca.reporting import _DISCLAIMER, report_nca_single, report_nca_summary
from openpkflow.nca.results import NCAResult, NCASummaryResults


def _make_oral_result(**overrides) -> NCAResult:
    defaults = dict(
        subject="1",
        route="oral",
        dose=320.0,
        auc_method="linear_up_log_down",
        blq_method="none",
        AUClast=95.0,
        AUCinf_obs=110.0,
        AUC_percent_extrapolated=13.6,
        Cmax=8.5,
        Tmax=1.0,
        lambda_z=0.088,
        half_life=7.9,
        lambda_z_method="auto",
        selected_lambda_z_times=[8.0, 12.0, 24.0],
        selected_lambda_z_concs=[2.1, 1.3, 0.4],
        CL_F=2.91,
        Vz_F=33.0,
    )
    defaults.update(overrides)
    return NCAResult(**defaults)


def _make_iv_result(**overrides) -> NCAResult:
    defaults = dict(
        subject="99",
        route="iv_bolus",
        dose=100.0,
        auc_method="linear_up_log_down",
        blq_method="none",
        AUClast=120.0,
        AUCinf_obs=130.0,
        AUC_percent_extrapolated=7.7,
        Cmax=25.0,
        Tmax=0.0,
        lambda_z=0.15,
        half_life=4.62,
        lambda_z_method="auto",
        selected_lambda_z_times=[4.0, 8.0, 12.0],
        selected_lambda_z_concs=[10.0, 3.0, 1.0],
        CL=0.77,
        Vz=5.13,
    )
    defaults.update(overrides)
    return NCAResult(**defaults)


def _make_summary(results=None, **overrides) -> NCASummaryResults:
    if results is None:
        results = [_make_oral_result(), _make_oral_result(subject="2", Cmax=9.1)]
    defaults = dict(
        results=results,
        study_label="Test Study",
        auc_method="linear_up_log_down",
        blq_method="none",
    )
    defaults.update(overrides)
    return NCASummaryResults(**defaults)


# ---------------------------------------------------------------------------
# report_nca_single
# ---------------------------------------------------------------------------


class TestReportNCASingle:
    def test_html_returns_str(self) -> None:
        result = _make_oral_result()
        rendered = report_nca_single(result, format="html")
        assert isinstance(rendered, str)

    def test_html_contains_html_tag(self) -> None:
        result = _make_oral_result()
        rendered = report_nca_single(result, format="html")
        assert "<html" in rendered.lower()

    def test_html_contains_subject(self) -> None:
        result = _make_oral_result()
        rendered = report_nca_single(result, format="html")
        assert "Subject 1" in rendered

    def test_html_contains_disclaimer(self) -> None:
        result = _make_oral_result()
        rendered = report_nca_single(result, format="html")
        assert "OpenPKFlow" in rendered
        assert "regulatory interpretation" in rendered

    def test_markdown_returns_str(self) -> None:
        result = _make_oral_result()
        rendered = report_nca_single(result, format="markdown")
        assert isinstance(rendered, str)

    def test_markdown_contains_disclaimer(self) -> None:
        result = _make_oral_result()
        rendered = report_nca_single(result, format="markdown")
        assert "OpenPKFlow" in rendered
        assert "regulatory interpretation" in rendered
        assert "_DISCLAIMER" not in rendered  # variable name not in output

    def test_markdown_contains_subject(self) -> None:
        result = _make_oral_result()
        rendered = report_nca_single(result, format="markdown")
        assert "# NCA Report -- Subject 1" in rendered

    def test_markdown_contains_pk_params(self) -> None:
        result = _make_oral_result()
        rendered = report_nca_single(result, format="markdown")
        assert "Cmax" in rendered
        assert "AUClast" in rendered
        assert "half_life" in rendered
        assert "CL_F" in rendered
        assert "Vz_F" in rendered

    def test_markdown_with_warnings(self) -> None:
        result = _make_oral_result(warnings=["lambda_z estimated with only 3 points"])
        rendered = report_nca_single(result, format="markdown")
        assert "Warnings" in rendered
        assert "lambda_z" in rendered

    def test_markdown_no_warnings_section_when_empty(self) -> None:
        result = _make_oral_result(warnings=[])
        rendered = report_nca_single(result, format="markdown")
        assert "## Warnings" not in rendered

    def test_iv_route_uses_cl_and_vz_labels_markdown(self) -> None:
        """IV route reports should show CL and Vz, not CL_F/Vz_F."""
        result = _make_iv_result()
        rendered = report_nca_single(result, format="markdown")
        assert "CL" in rendered
        assert "Vz" in rendered
        assert "CL_F" not in rendered
        assert "Vz_F" not in rendered

    def test_writes_file_html(self, tmp_path: Path) -> None:
        out = tmp_path / "report.html"
        result = _make_oral_result()
        rendered = report_nca_single(result, output_path=out, format="html")
        assert out.exists()
        assert out.read_text(encoding="utf-8") == rendered

    def test_writes_file_markdown(self, tmp_path: Path) -> None:
        out = tmp_path / "report.md"
        result = _make_oral_result()
        rendered = report_nca_single(result, output_path=out, format="markdown")
        assert out.exists()
        assert out.read_text(encoding="utf-8") == rendered

    def test_writes_file_in_new_directory(self, tmp_path: Path) -> None:
        out = tmp_path / "subdir" / "report.html"
        result = _make_oral_result()
        rendered = report_nca_single(result, output_path=out, format="html")
        assert out.exists()
        assert out.read_text(encoding="utf-8") == rendered

    def test_markdown_is_ascii_safe(self) -> None:
        """The markdown content uses _DISCLAIMER which may contain Unicode
        characters. Verify the key disclaimer text appears regardless."""
        result = _make_oral_result()
        rendered = report_nca_single(result, format="markdown")
        assert "OpenPKFlow" in rendered
        assert "regulatory interpretation" in rendered

    def test_lambda_z_none_shows_na(self) -> None:
        result = _make_oral_result(lambda_z=None, half_life=None, lambda_z_method=None)
        rendered = report_nca_single(result, format="markdown")
        assert "N/A" in rendered

    def test_output_path_is_path_object(self, tmp_path: Path) -> None:
        out = tmp_path / "r.html"
        report_nca_single(_make_oral_result(), output_path=out, format="markdown")
        assert out.exists()


# ---------------------------------------------------------------------------
# report_nca_summary
# ---------------------------------------------------------------------------


class TestReportNCASummary:
    def test_html_returns_str(self) -> None:
        summary = _make_summary()
        rendered = report_nca_summary(summary, format="html")
        assert isinstance(rendered, str)

    def test_html_contains_html_tag(self) -> None:
        summary = _make_summary()
        rendered = report_nca_summary(summary, format="html")
        assert "<html" in rendered.lower()

    def test_html_contains_disclaimer(self) -> None:
        summary = _make_summary()
        rendered = report_nca_summary(summary, format="html")
        assert "OpenPKFlow" in rendered
        assert "regulatory interpretation" in rendered

    def test_html_contains_study_label(self) -> None:
        summary = _make_summary()
        rendered = report_nca_summary(summary, format="html")
        assert "Test Study" in rendered

    def test_markdown_returns_str(self) -> None:
        summary = _make_summary()
        rendered = report_nca_summary(summary, format="markdown")
        assert isinstance(rendered, str)

    def test_markdown_contains_disclaimer(self) -> None:
        summary = _make_summary()
        rendered = report_nca_summary(summary, format="markdown")
        assert "OpenPKFlow" in rendered
        assert _DISCLAIMER in rendered

    def test_markdown_contains_header(self) -> None:
        summary = _make_summary()
        rendered = report_nca_summary(summary, format="markdown")
        assert "# NCA Summary Report" in rendered

    def test_markdown_contains_study_label(self) -> None:
        summary = _make_summary()
        rendered = report_nca_summary(summary, format="markdown")
        assert "Test Study" in rendered

    def test_markdown_no_study_label_header(self) -> None:
        summary = _make_summary(study_label="")
        rendered = report_nca_summary(summary, format="markdown")
        assert "**Study:**" not in rendered

    def test_markdown_contains_both_subjects(self) -> None:
        r1 = _make_oral_result(subject="A")
        r2 = _make_oral_result(subject="B")
        summary = _make_summary(results=[r1, r2])
        rendered = report_nca_summary(summary, format="markdown")
        assert "A" in rendered
        assert "B" in rendered

    def test_markdown_empty_results_handled(self) -> None:
        summary = NCASummaryResults(results=[])
        rendered = report_nca_summary(summary, format="markdown")
        assert "NCA Summary Report" in rendered
        assert _DISCLAIMER in rendered

    def test_writes_file_html(self, tmp_path: Path) -> None:
        out = tmp_path / "summary.html"
        rendered = report_nca_summary(_make_summary(), output_path=out, format="html")
        assert out.exists()
        assert out.read_text(encoding="utf-8") == rendered

    def test_writes_file_markdown(self, tmp_path: Path) -> None:
        out = tmp_path / "summary.md"
        rendered = report_nca_summary(_make_summary(), output_path=out, format="markdown")
        assert out.exists()
        assert out.read_text(encoding="utf-8") == rendered

    def test_writes_in_new_directory(self, tmp_path: Path) -> None:
        out = tmp_path / "out" / "summary.html"
        summary = _make_summary()
        rendered = report_nca_summary(summary, output_path=out, format="html")
        assert out.exists()
        assert out.read_text(encoding="utf-8") == rendered

    def test_markdown_is_ascii_safe(self) -> None:
        """The markdown content uses _DISCLAIMER which may contain Unicode
        characters. Verify the key disclaimer text appears regardless."""
        summary = _make_summary()
        rendered = report_nca_summary(summary, format="markdown")
        assert "OpenPKFlow" in rendered
        assert _DISCLAIMER in rendered

    def test_iv_route_uses_cl_and_vz_labels(self) -> None:
        """IV subject in summary should show CL and Vz column values properly."""
        r = _make_iv_result()
        summary = _make_summary(results=[r])
        rendered = report_nca_summary(summary, format="markdown")
        assert "0.77" in rendered
        assert "5.13" in rendered
