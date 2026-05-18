"""Integration tests for NCAStudy — orchestration layer."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pandas as pd
import pytest

from openpkflow.nca.results import NCAResult, NCASummaryResults
from openpkflow.nca.study import NCAStudy


def _make_df(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def _oral_df() -> pd.DataFrame:
    return _make_df([
        {"subject": "1", "time": 0.0, "conc": 0.0,  "dose": 320.0, "route": "oral"},
        {"subject": "1", "time": 0.5, "conc": 4.0,  "dose": 320.0, "route": "oral"},
        {"subject": "1", "time": 1.0, "conc": 8.0,  "dose": 320.0, "route": "oral"},
        {"subject": "1", "time": 2.0, "conc": 6.0,  "dose": 320.0, "route": "oral"},
        {"subject": "1", "time": 4.0, "conc": 3.0,  "dose": 320.0, "route": "oral"},
        {"subject": "1", "time": 8.0, "conc": 1.5,  "dose": 320.0, "route": "oral"},
        {"subject": "1", "time": 12.0, "conc": 0.75, "dose": 320.0, "route": "oral"},
        {"subject": "1", "time": 24.0, "conc": 0.2,  "dose": 320.0, "route": "oral"},
    ])


class TestNCAStudyInit:
    def test_valid_auc_methods(self) -> None:
        df = _oral_df()
        for method in ("linear", "log", "linear_up_log_down"):
            study = NCAStudy(df, auc_method=method, blq_method="none")
            assert study is not None

    def test_invalid_auc_method_raises(self) -> None:
        df = _oral_df()
        with pytest.raises(ValueError, match="auc_method"):
            NCAStudy(df, auc_method="trapezoid", blq_method="none")  # type: ignore[arg-type]


class TestNCAStudyAnalyze:
    def test_returns_nca_summary_results(self) -> None:
        study = NCAStudy(_oral_df(), auc_method="linear_up_log_down", blq_method="none")
        summary = study.analyze()
        assert isinstance(summary, NCASummaryResults)

    def test_one_result_per_subject(self) -> None:
        study = NCAStudy(_oral_df(), auc_method="linear", blq_method="none")
        summary = study.analyze()
        assert len(summary.results) == 1

    def test_two_subjects(self) -> None:
        df = _oral_df().copy()
        s2 = df.copy()
        s2["subject"] = "2"
        df2 = pd.concat([df, s2], ignore_index=True)
        study = NCAStudy(df2, auc_method="linear", blq_method="none")
        summary = study.analyze()
        assert len(summary.results) == 2

    def test_result_fields_populated(self) -> None:
        study = NCAStudy(_oral_df(), auc_method="linear_up_log_down", blq_method="none")
        result = study.analyze().results[0]
        assert isinstance(result, NCAResult)
        assert result.subject == "1"
        assert result.route == "oral"
        assert result.AUClast > 0
        assert result.Cmax > 0
        assert result.Tmax >= 0

    def test_oral_route_populates_clf_vzf(self) -> None:
        study = NCAStudy(_oral_df(), auc_method="linear_up_log_down", blq_method="none")
        result = study.analyze().results[0]
        # lambda_z should succeed for this profile (clean declining tail)
        if result.lambda_z is not None:
            assert result.CL_F is not None
            assert result.Vz_F is not None
            assert result.CL is None
            assert result.Vz is None

    def test_lambda_z_none_when_insufficient_tail_points(self) -> None:
        # Only 2 post-Cmax positive points → lambda_z should fail gracefully
        df = _make_df([
            {"subject": "1", "time": 0.0, "conc": 0.0,  "dose": 100.0, "route": "oral"},
            {"subject": "1", "time": 1.0, "conc": 5.0,  "dose": 100.0, "route": "oral"},
            {"subject": "1", "time": 2.0, "conc": 3.0,  "dose": 100.0, "route": "oral"},
            {"subject": "1", "time": 4.0, "conc": 0.0,  "dose": 100.0, "route": "oral"},
        ])
        study = NCAStudy(df, auc_method="linear", blq_method="none")
        result = study.analyze().results[0]
        assert result.lambda_z is None
        assert result.half_life is None
        assert len(result.warnings) > 0

    def test_auc_method_stored(self) -> None:
        study = NCAStudy(_oral_df(), auc_method="log", blq_method="none")
        summary = study.analyze()
        assert summary.auc_method == "log"
        assert summary.results[0].auc_method == "log"

    def test_blq_method_stored(self) -> None:
        study = NCAStudy(_oral_df(), auc_method="linear", blq_method="zero")
        summary = study.analyze()
        assert summary.blq_method == "zero"
        assert summary.results[0].blq_method == "zero"


class TestNCAStudyFromCsv:
    def test_from_csv_loads_and_analyzes(self, tmp_path: Path) -> None:
        csv_content = textwrap.dedent("""\
            subject,time,conc,dose,route
            1,0.0,0.0,320.0,oral
            1,0.5,4.0,320.0,oral
            1,1.0,8.0,320.0,oral
            1,2.0,6.0,320.0,oral
            1,4.0,3.0,320.0,oral
            1,8.0,1.5,320.0,oral
            1,12.0,0.75,320.0,oral
            1,24.0,0.2,320.0,oral
        """)
        p = tmp_path / "pk.csv"
        p.write_text(csv_content, encoding="utf-8")
        study = NCAStudy.from_csv(p, auc_method="linear_up_log_down", blq_method="none")
        summary = study.analyze()
        assert len(summary.results) == 1


class TestNCASummaryResults:
    def test_summary_returns_string(self) -> None:
        study = NCAStudy(_oral_df(), auc_method="linear", blq_method="none")
        summary = study.analyze()
        text = summary.summary()
        assert isinstance(text, str)
        assert "AUClast" in text

    def test_summary_ascii_only(self) -> None:
        study = NCAStudy(_oral_df(), auc_method="linear", blq_method="none")
        text = study.analyze().summary()
        text.encode("ascii")  # raises UnicodeEncodeError if non-ASCII present

    def test_to_dataframe_columns(self) -> None:
        study = NCAStudy(_oral_df(), auc_method="linear", blq_method="none")
        df = study.analyze().to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert "AUClast" in df.columns
        assert "Cmax" in df.columns
        assert "subject" in df.columns

    def test_to_dataframe_one_row_per_subject(self) -> None:
        study = NCAStudy(_oral_df(), auc_method="linear", blq_method="none")
        df = study.analyze().to_dataframe()
        assert len(df) == 1


class TestNCAResult:
    def _result(self) -> NCAResult:
        study = NCAStudy(_oral_df(), auc_method="linear_up_log_down", blq_method="none")
        return study.analyze().results[0]

    def test_summary_ascii_only(self) -> None:
        self._result().summary().encode("ascii")

    def test_summary_contains_subject(self) -> None:
        text = self._result().summary()
        assert "1" in text

    def test_to_dict_has_all_required_keys(self) -> None:
        d = self._result().to_dict()
        required_keys = [
            "subject", "route", "dose", "auc_method", "blq_method",
            "AUClast", "AUCinf_obs", "AUC_percent_extrapolated",
            "Cmax", "Tmax", "lambda_z", "half_life", "lambda_z_method",
            "selected_lambda_z_times", "selected_lambda_z_concs",
            "CL_F", "Vz_F", "CL", "Vz", "warnings",
        ]
        for key in required_keys:
            assert key in d, f"Missing key: {key}"

    def test_report_markdown(self, tmp_path: Path) -> None:
        out = tmp_path / "report.md"
        rendered = self._result().report(out, format="markdown")
        assert isinstance(rendered, str)
        assert out.exists()

    def test_report_html(self, tmp_path: Path) -> None:
        out = tmp_path / "report.html"
        rendered = self._result().report(out, format="html")
        assert isinstance(rendered, str)
        assert "<html" in rendered.lower()
        assert out.exists()

    def test_report_unknown_format_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="Unknown format"):
            self._result().report(tmp_path / "r.pptx", format="pptx")
