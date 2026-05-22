"""Tests for openpkflow.be.study and openpkflow.be.results."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from openpkflow.be import BEStudy


def _make_df(
    n: int = 8,
    gmr_true: float = 0.95,
    cv_intra: float = 0.10,
    seq_balanced: bool = True,
) -> pd.DataFrame:
    """Generate a synthetic balanced 2x2 crossover BE dataset."""
    import math
    import random

    random.seed(42)
    subjects = [f"S{i + 1:02d}" for i in range(n)]
    sequences = (["RT"] * (n // 2) + ["TR"] * (n // 2)) if seq_balanced else ["RT"] * n

    rows = []
    for i, subj in enumerate(subjects):
        ref = 100.0 + random.gauss(0, 5)
        # within-subject ratio drawn from log-normal centred on gmr_true
        log_ratio = math.log(gmr_true) + random.gauss(0, cv_intra)
        tst = ref * math.exp(log_ratio)
        rows.append(
            {
                "subject": subj,
                "sequence": sequences[i],
                "reference": round(ref, 4),
                "test": round(tst, 4),
            }
        )
    return pd.DataFrame(rows)


class TestBEStudyInit:
    def test_basic_construction(self) -> None:
        df = _make_df()
        study = BEStudy(df, parameter="AUCinf")
        assert study is not None

    def test_missing_required_column_raises(self) -> None:
        df = _make_df().drop(columns=["reference"])
        with pytest.raises(ValueError, match="reference"):
            BEStudy(df, parameter="AUCinf")

    def test_missing_sequence_col_tolerated(self) -> None:
        """sequence column absent -> silently dropped, analysis still works."""
        df = _make_df().drop(columns=["sequence"])
        study = BEStudy(df, parameter="AUCinf", sequence_col="sequence")
        result = study.analyze()
        assert "sequence" not in result.subjects_df.columns


class TestBEStudyAnalyze:
    def test_returns_be_result(self) -> None:
        from openpkflow.be.results import BEResult

        df = _make_df(gmr_true=0.95, cv_intra=0.10)
        result = BEStudy(df, parameter="AUCinf").analyze()
        assert isinstance(result, BEResult)

    def test_gmr_close_to_true_gmr(self) -> None:
        """With n=20 and 10% CV, estimated GMR should be within 10% of truth."""
        df = _make_df(n=20, gmr_true=0.95, cv_intra=0.10)
        result = BEStudy(df, parameter="AUCinf").analyze()
        assert result.gmr == pytest.approx(0.95, rel=0.10)

    def test_parameter_label_propagated(self) -> None:
        df = _make_df()
        result = BEStudy(df, parameter="Cmax").analyze()
        assert result.parameter == "Cmax"

    def test_n_equals_subject_count(self) -> None:
        n = 12
        df = _make_df(n=n)
        result = BEStudy(df, parameter="AUCinf").analyze()
        assert result.n == n

    def test_ci_lower_le_gmr_le_ci_upper(self) -> None:
        df = _make_df()
        r = BEStudy(df, parameter="AUCinf").analyze()
        assert r.gmr_lower_90ci <= r.gmr <= r.gmr_upper_90ci

    def test_custom_be_limits(self) -> None:
        """NTI limits: T/R = 0.88 passes standard 80-125% but fails NTI 90-111.11%."""
        ref = [100.0] * 8
        tst = [88.0] * 8
        df = pd.DataFrame({"subject": [f"S{i}" for i in range(8)], "reference": ref, "test": tst})
        r_standard = BEStudy(df, parameter="AUCinf", sequence_col=None).analyze(
            be_lower=0.80, be_upper=1.25
        )
        r_nti = BEStudy(df, parameter="AUCinf", sequence_col=None).analyze(
            be_lower=0.90, be_upper=1.1111
        )
        assert r_standard.bioequivalent is True
        assert r_nti.bioequivalent is False

    def test_subjects_df_has_expected_columns(self) -> None:
        df = _make_df()
        result = BEStudy(df, parameter="AUCinf").analyze()
        for col in ("subject", "sequence", "reference", "test", "ratio", "log_diff"):
            assert col in result.subjects_df.columns

    def test_subjects_df_ratio_equals_test_over_ref(self) -> None:
        df = _make_df()
        result = BEStudy(df, parameter="AUCinf").analyze()
        for _, row in result.subjects_df.iterrows():
            assert row["ratio"] == pytest.approx(row["test"] / row["reference"], rel=1e-6)

    def test_to_bioeqpy_dataframe_returns_long_format(self) -> None:
        df = pd.DataFrame(
            {
                "subject": ["S1", "S2"],
                "sequence": ["TR", "RT"],
                "reference": [100.0, 110.0],
                "test": [95.0, 104.5],
            }
        )
        table = BEStudy(df, parameter="AUCinf").to_bioeqpy_dataframe()

        assert list(table.columns) == ["subject", "sequence", "period", "treatment", "AUCinf"]
        assert len(table) == 4
        assert table[table["subject"] == "S1"]["treatment"].tolist() == ["T", "R"]
        assert table[table["subject"] == "S1"]["AUCinf"].tolist() == [95.0, 100.0]
        assert table[table["subject"] == "S2"]["treatment"].tolist() == ["R", "T"]
        assert table[table["subject"] == "S2"]["AUCinf"].tolist() == [110.0, 104.5]

    def test_to_bioeqpy_dataframe_requires_sequence(self) -> None:
        df = pd.DataFrame({"subject": ["S1"], "reference": [100.0], "test": [95.0]})
        study = BEStudy(df, parameter="AUCinf", sequence_col=None)

        with pytest.raises(ValueError, match="sequence"):
            study.to_bioeqpy_dataframe()

    def test_to_bioeqpy_dataframe_rejects_unknown_sequence(self) -> None:
        df = pd.DataFrame(
            {"subject": ["S1"], "sequence": ["TT"], "reference": [100.0], "test": [95.0]}
        )

        with pytest.raises(ValueError, match="TR/RT"):
            BEStudy(df, parameter="AUCinf").to_bioeqpy_dataframe()

    def test_to_bioeqpy_csv_writes_export(self, tmp_path: Path) -> None:
        df = pd.DataFrame(
            {"subject": ["S1"], "sequence": ["TR"], "reference": [100.0], "test": [95.0]}
        )
        out = tmp_path / "bioeqpy_input.csv"
        BEStudy(df, parameter="AUCinf").to_bioeqpy_csv(out)

        assert "period,treatment,AUCinf" in out.read_text(encoding="utf-8")


class TestBEStudySummary:
    def test_summary_contains_gmr(self) -> None:
        df = _make_df()
        result = BEStudy(df, parameter="AUCinf").analyze()
        assert "GMR" in result.summary()

    def test_summary_contains_conclusion(self) -> None:
        df = _make_df()
        result = BEStudy(df, parameter="AUCinf").analyze()
        summary = result.summary()
        assert "BIOEQUIVALENT" in summary or "NOT BIOEQUIVALENT" in summary


class TestBEStudyReport:
    def test_html_report_created(self, tmp_path: Path) -> None:
        df = _make_df()
        result = BEStudy(df, parameter="AUCinf").analyze()
        out = tmp_path / "be_report.html"
        result.report(out)
        assert out.exists()
        text = out.read_text(encoding="utf-8")
        assert "Bioequivalence" in text
        assert "GMR" in text

    def test_markdown_report_created(self, tmp_path: Path) -> None:
        df = _make_df()
        result = BEStudy(df, parameter="AUCinf").analyze()
        out = tmp_path / "be_report.md"
        result.report(out)
        assert out.exists()
        text = out.read_text(encoding="utf-8")
        assert "GMR" in text
        assert "BIOEQUIVALENT" in text or "NOT BIOEQUIVALENT" in text

    def test_html_report_explicit_format(self, tmp_path: Path) -> None:
        df = _make_df()
        result = BEStudy(df, parameter="AUCinf").analyze()
        out = tmp_path / "report.txt"
        result.report(out, format="html")
        assert out.exists()

    def test_unsupported_format_raises(self, tmp_path: Path) -> None:
        df = _make_df()
        result = BEStudy(df, parameter="AUCinf").analyze()
        with pytest.raises(ValueError, match="Unsupported"):
            result.report(tmp_path / "out.pdf", format="pdf")


class TestBEStudyFromNCA:
    def test_from_nca_results_basic(self) -> None:
        """from_nca_results should build a BEStudy matching subjects by ID."""
        import math

        from openpkflow.nca.results import NCAResult, NCASummaryResults

        def _make_nca(subjects: list[str], scale: float) -> NCASummaryResults:
            results = [
                NCAResult(
                    subject=s,
                    route="oral",
                    dose=100.0,
                    auc_method="linear",
                    blq_method="none",
                    AUClast=80.0 * scale,
                    AUCinf_obs=100.0 * scale,
                    AUC_percent_extrapolated=20.0,
                    Cmax=10.0 * scale,
                    Tmax=2.0,
                    lambda_z=0.1,
                    half_life=math.log(2) / 0.1,
                    lambda_z_method="auto",
                    selected_lambda_z_times=[8.0, 12.0, 24.0],
                    selected_lambda_z_concs=[2.0, 1.0, 0.2],
                    CL_F=1.0,
                    Vz_F=10.0,
                    CL=None,
                    Vz=None,
                    warnings=[],
                )
                for s in subjects
            ]
            return NCASummaryResults(results=results, auc_method="linear", blq_method="none")

        ref_res = _make_nca(["S1", "S2", "S3"], scale=1.0)
        tst_res = _make_nca(["S1", "S2", "S3"], scale=0.90)

        study = BEStudy.from_nca_results(ref_res, tst_res, parameter="AUCinf")
        result = study.analyze()
        assert result.n == 3
        assert result.gmr == pytest.approx(0.90, abs=1e-9)

    def test_from_nca_no_common_subjects_raises(self) -> None:
        import math

        from openpkflow.nca.results import NCAResult, NCASummaryResults

        def _minimal(subj: str) -> NCAResult:
            return NCAResult(
                subject=subj,
                route="oral",
                dose=100.0,
                auc_method="linear",
                blq_method="none",
                AUClast=80.0,
                AUCinf_obs=100.0,
                AUC_percent_extrapolated=20.0,
                Cmax=10.0,
                Tmax=2.0,
                lambda_z=0.1,
                half_life=math.log(2) / 0.1,
                lambda_z_method="auto",
                selected_lambda_z_times=[],
                selected_lambda_z_concs=[],
                CL_F=1.0,
                Vz_F=10.0,
                CL=None,
                Vz=None,
                warnings=[],
            )

        ref_res = NCASummaryResults(results=[_minimal("A")], auc_method="linear", blq_method="none")
        tst_res = NCASummaryResults(results=[_minimal("B")], auc_method="linear", blq_method="none")
        with pytest.raises(ValueError, match="No subjects"):
            BEStudy.from_nca_results(ref_res, tst_res, parameter="AUCinf")
