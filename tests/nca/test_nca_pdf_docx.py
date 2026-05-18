"""Tests for NCA PDF and DOCX report renderers.

PDF magic bytes: b"%PDF" (ISO 32000)
DOCX magic bytes: b"PK" (ZIP container, OOXML)
"""
from __future__ import annotations

import pytest

from openpkflow.nca.results import NCAResult, NCASummaryResults

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def _make_result(lambda_z: float | None = 0.088, warnings: list[str] | None = None) -> NCAResult:
    return NCAResult(
        subject="1",
        route="oral",
        dose=320.0,
        auc_method="linear_up_log_down",
        blq_method="none",
        AUClast=95.0,
        AUCinf_obs=110.0 if lambda_z else None,
        AUC_percent_extrapolated=13.6 if lambda_z else None,
        Cmax=8.5,
        Tmax=1.0,
        lambda_z=lambda_z,
        half_life=7.9 if lambda_z else None,
        lambda_z_method="auto" if lambda_z else None,
        selected_lambda_z_times=[8.0, 12.0, 24.0] if lambda_z else [],
        selected_lambda_z_concs=[2.1, 1.3, 0.4] if lambda_z else [],
        CL_F=2.91,
        Vz_F=33.0,
        warnings=warnings or [],
    )


def _make_summary() -> NCASummaryResults:
    results = [
        _make_result(),
        NCAResult(
            subject="2",
            route="oral",
            dose=320.0,
            auc_method="linear_up_log_down",
            blq_method="none",
            AUClast=108.0,
            AUCinf_obs=125.0,
            AUC_percent_extrapolated=13.6,
            Cmax=9.1,
            Tmax=1.5,
            lambda_z=0.079,
            half_life=8.8,
            lambda_z_method="auto",
            selected_lambda_z_times=[8.0, 12.0, 24.0],
            selected_lambda_z_concs=[2.4, 1.6, 0.5],
            CL_F=2.56,
            Vz_F=32.4,
        ),
    ]
    return NCASummaryResults(
        results=results,
        study_label="Theoph Test",
        auc_method="linear_up_log_down",
        blq_method="none",
    )


# ---------------------------------------------------------------------------
# PDF tests
# ---------------------------------------------------------------------------

reportlab = pytest.importorskip("reportlab", reason="reportlab not installed")

from openpkflow.report.pdf import (  # noqa: E402
    render_nca_single_pdf_report,
    render_nca_summary_pdf_report,
)


class TestNCASinglePDF:
    def test_returns_bytes(self):
        result = _make_result()
        pdf = render_nca_single_pdf_report(result=result)
        assert isinstance(pdf, bytes)

    def test_pdf_magic_bytes(self):
        result = _make_result()
        pdf = render_nca_single_pdf_report(result=result)
        assert pdf[:4] == b"%PDF"

    def test_nonempty(self):
        result = _make_result()
        pdf = render_nca_single_pdf_report(result=result)
        assert len(pdf) > 1000

    def test_writes_file(self, tmp_path):
        result = _make_result()
        out = tmp_path / "nca_sub1.pdf"
        pdf = render_nca_single_pdf_report(result=result, output_path=out)
        assert out.exists()
        assert out.read_bytes() == pdf

    def test_lambda_z_none(self):
        result = _make_result(lambda_z=None)
        pdf = render_nca_single_pdf_report(result=result)
        assert pdf[:4] == b"%PDF"

    def test_with_warnings(self):
        result = _make_result(warnings=["lambda_z estimation used only 3 points"])
        pdf = render_nca_single_pdf_report(result=result)
        assert pdf[:4] == b"%PDF"

    def test_dispatch_via_result_report(self, tmp_path):
        result = _make_result()
        out = tmp_path / "sub1.pdf"
        content = result.report(out, format="pdf")
        assert isinstance(content, bytes)
        assert content[:4] == b"%PDF"
        assert out.exists()


class TestNCASummaryPDF:
    def test_returns_bytes(self):
        summary = _make_summary()
        pdf = render_nca_summary_pdf_report(summary=summary)
        assert isinstance(pdf, bytes)

    def test_pdf_magic_bytes(self):
        summary = _make_summary()
        pdf = render_nca_summary_pdf_report(summary=summary)
        assert pdf[:4] == b"%PDF"

    def test_nonempty(self):
        summary = _make_summary()
        pdf = render_nca_summary_pdf_report(summary=summary)
        assert len(pdf) > 1000

    def test_writes_file(self, tmp_path):
        summary = _make_summary()
        out = tmp_path / "nca_summary.pdf"
        pdf = render_nca_summary_pdf_report(summary=summary, output_path=out)
        assert out.exists()
        assert out.read_bytes() == pdf

    def test_dispatch_via_summary_report(self, tmp_path):
        summary = _make_summary()
        out = tmp_path / "summary.pdf"
        content = summary.report(out, format="pdf")
        assert isinstance(content, bytes)
        assert content[:4] == b"%PDF"
        assert out.exists()

    def test_no_study_label(self):
        summary = NCASummaryResults(
            results=[_make_result()],
            study_label="",
            auc_method="linear_up_log_down",
            blq_method="none",
        )
        pdf = render_nca_summary_pdf_report(summary=summary)
        assert pdf[:4] == b"%PDF"


# ---------------------------------------------------------------------------
# DOCX tests
# ---------------------------------------------------------------------------

docx_pkg = pytest.importorskip("docx", reason="python-docx not installed")

from openpkflow.report.docx import (  # noqa: E402
    render_nca_single_docx_report,
    render_nca_summary_docx_report,
)

_DOCX_MAGIC = b"PK"


class TestNCASingleDOCX:
    def test_returns_bytes(self):
        result = _make_result()
        docx = render_nca_single_docx_report(result=result)
        assert isinstance(docx, bytes)

    def test_docx_magic_bytes(self):
        result = _make_result()
        docx = render_nca_single_docx_report(result=result)
        assert docx[:2] == _DOCX_MAGIC

    def test_nonempty(self):
        result = _make_result()
        docx = render_nca_single_docx_report(result=result)
        assert len(docx) > 1000

    def test_writes_file(self, tmp_path):
        result = _make_result()
        out = tmp_path / "nca_sub1.docx"
        docx = render_nca_single_docx_report(result=result, output_path=out)
        assert out.exists()
        assert out.read_bytes() == docx

    def test_lambda_z_none(self):
        result = _make_result(lambda_z=None)
        docx = render_nca_single_docx_report(result=result)
        assert docx[:2] == _DOCX_MAGIC

    def test_with_warnings(self):
        result = _make_result(warnings=["lambda_z used only 3 points"])
        docx = render_nca_single_docx_report(result=result)
        assert docx[:2] == _DOCX_MAGIC

    def test_dispatch_via_result_report(self, tmp_path):
        result = _make_result()
        out = tmp_path / "sub1.docx"
        content = result.report(out, format="docx")
        assert isinstance(content, bytes)
        assert content[:2] == _DOCX_MAGIC
        assert out.exists()

    def test_disclaimer_in_document(self, tmp_path):
        import zipfile

        result = _make_result()
        out = tmp_path / "sub1.docx"
        render_nca_single_docx_report(result=result, output_path=out)
        with zipfile.ZipFile(out) as zf:
            doc_xml = zf.read("word/document.xml").decode("utf-8")
        assert "OpenPKFlow" in doc_xml


class TestNCASummaryDOCX:
    def test_returns_bytes(self):
        summary = _make_summary()
        docx = render_nca_summary_docx_report(summary=summary)
        assert isinstance(docx, bytes)

    def test_docx_magic_bytes(self):
        summary = _make_summary()
        docx = render_nca_summary_docx_report(summary=summary)
        assert docx[:2] == _DOCX_MAGIC

    def test_writes_file(self, tmp_path):
        summary = _make_summary()
        out = tmp_path / "nca_summary.docx"
        docx = render_nca_summary_docx_report(summary=summary, output_path=out)
        assert out.exists()
        assert out.read_bytes() == docx

    def test_dispatch_via_summary_report(self, tmp_path):
        summary = _make_summary()
        out = tmp_path / "summary.docx"
        content = summary.report(out, format="docx")
        assert isinstance(content, bytes)
        assert content[:2] == _DOCX_MAGIC
        assert out.exists()

    def test_no_study_label(self):
        summary = NCASummaryResults(
            results=[_make_result()],
            study_label="",
            auc_method="linear_up_log_down",
            blq_method="none",
        )
        docx = render_nca_summary_docx_report(summary=summary)
        assert docx[:2] == _DOCX_MAGIC
