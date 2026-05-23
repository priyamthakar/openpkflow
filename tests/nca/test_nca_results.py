"""Tests for nca/results.py -- NCAResult and NCASummaryResults methods."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

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


# ---------------------------------------------------------------------------
# NCAResult.to_dict
# ---------------------------------------------------------------------------


class TestNCAResultToDict:
    """Tests for NCAResult.to_dict().

    Reference: openpkflow NCA data model.
    """

    def test_all_basic_keys_present(self) -> None:
        r = _make_oral_result()
        d = r.to_dict()
        for key in (
            "subject",
            "route",
            "dose",
            "auc_method",
            "blq_method",
            "AUClast",
            "AUCinf_obs",
            "AUC_percent_extrapolated",
            "Cmax",
            "Tmax",
            "lambda_z",
            "half_life",
            "lambda_z_method",
        ):
            assert key in d

    def test_clf_vzf_present_when_oral(self) -> None:
        r = _make_oral_result()
        d = r.to_dict()
        assert d["CL_F"] == 2.91
        assert d["Vz_F"] == 33.0
        assert d["CL"] is None
        assert d["Vz"] is None

    def test_cl_vz_present_when_iv(self) -> None:
        r = NCAResult(
            subject="99",
            route="iv_bolus",
            dose=100.0,
            auc_method="linear",
            blq_method="none",
            AUClast=120.0,
            AUCinf_obs=130.0,
            AUC_percent_extrapolated=7.7,
            Cmax=25.0,
            Tmax=0.0,
            lambda_z=0.15,
            half_life=4.62,
            lambda_z_method="auto",
            CL=0.77,
            Vz=5.13,
        )
        d = r.to_dict()
        assert d["CL"] == 0.77
        assert d["Vz"] == 5.13
        assert d["CL_F"] is None
        assert d["Vz_F"] is None

    def test_lambda_z_none_yields_none(self) -> None:
        r = _make_oral_result(lambda_z=None, half_life=None, lambda_z_method=None)
        d = r.to_dict()
        assert d["lambda_z"] is None
        assert d["half_life"] is None

    def test_quality_metrics_keys(self) -> None:
        r = NCAResult(
            subject="1",
            route="oral",
            dose=100.0,
            auc_method="linear",
            blq_method="zero",
            AUClast=50.0,
            AUCinf_obs=60.0,
            AUC_percent_extrapolated=10.0,
            Cmax=10.0,
            Tmax=2.0,
            lambda_z=0.1,
            half_life=6.93,
            lambda_z_method="manual",
            lambda_z_adj_r2=0.95,
            lambda_z_n_points=3,
        )
        d = r.to_dict()
        assert d["lambda_z_adj_r2"] == 0.95
        assert d["lambda_z_n_points"] == 3

    def test_dose_normalised_keys(self) -> None:
        r = NCAResult(
            subject="1",
            route="oral",
            dose=100.0,
            auc_method="linear",
            blq_method="zero",
            AUClast=50.0,
            AUCinf_obs=60.0,
            AUC_percent_extrapolated=10.0,
            Cmax=10.0,
            Tmax=2.0,
            lambda_z=0.1,
            half_life=6.93,
            lambda_z_method="auto",
            DN_AUClast=0.5,
            DN_AUCinf_obs=0.6,
            DN_Cmax=0.1,
        )
        d = r.to_dict()
        assert d["DN_AUClast"] == 0.5
        assert d["DN_AUCinf_obs"] == 0.6
        assert d["DN_Cmax"] == 0.1

    def test_steady_state_keys(self) -> None:
        r = NCAResult(
            subject="1",
            route="oral",
            dose=100.0,
            auc_method="linear",
            blq_method="zero",
            AUClast=50.0,
            AUCinf_obs=60.0,
            AUC_percent_extrapolated=10.0,
            Cmax=10.0,
            Tmax=2.0,
            lambda_z=0.1,
            half_life=6.93,
            lambda_z_method="auto",
            Cmax_ss=12.0,
            Cmin_ss=4.0,
            Cavg_ss=8.0,
            AUCtau=96.0,
            fluctuation_pct=100.0,
            swing=2.0,
            accumulation_ratio=1.5,
        )
        d = r.to_dict()
        assert d["Cmax_ss"] == 12.0
        assert d["fluctuation_pct"] == 100.0
        assert d["accumulation_ratio"] == 1.5

    def test_urinary_excretion_keys(self) -> None:
        r = NCAResult(
            subject="1",
            route="iv_bolus",
            dose=100.0,
            auc_method="linear",
            blq_method="zero",
            AUClast=50.0,
            AUCinf_obs=60.0,
            AUC_percent_extrapolated=10.0,
            Cmax=10.0,
            Tmax=0.0,
            lambda_z=0.1,
            half_life=6.93,
            lambda_z_method="auto",
            CL=2.0,
            Vz=20.0,
            Ae=45.0,
            Ae_pct=45.0,
            CLr=0.9,
        )
        d = r.to_dict()
        assert d["Ae"] == 45.0
        assert d["Ae_pct"] == 45.0
        assert d["CLr"] == 0.9

    def test_warnings_key(self) -> None:
        r = _make_oral_result(warnings=["test warning"])
        d = r.to_dict()
        assert d["warnings"] == ["test warning"]

    def test_list_fields_are_lists(self) -> None:
        r = _make_oral_result()
        d = r.to_dict()
        assert isinstance(d["selected_lambda_z_times"], list)
        assert isinstance(d["selected_lambda_z_concs"], list)


# ---------------------------------------------------------------------------
# NCAResult.summary
# ---------------------------------------------------------------------------


class TestNCAResultSummary:
    def test_returns_string(self) -> None:
        r = _make_oral_result()
        s = r.summary()
        assert isinstance(s, str)

    def test_contains_subject(self) -> None:
        r = _make_oral_result(subject="ABC123")
        assert "ABC123" in r.summary()

    def test_contains_route_and_dose(self) -> None:
        r = _make_oral_result(route="oral", dose=320.0)
        s = r.summary()
        assert "oral" in s
        assert "320" in s

    def test_contains_pk_parameters(self) -> None:
        r = _make_oral_result()
        s = r.summary()
        assert "Cmax" in s
        assert "AUClast" in s
        assert "lambda_z" in s

    def test_ascii_safe(self) -> None:
        r = _make_oral_result()
        r.summary().encode("ascii")

    def test_shows_na_when_none_lambda_z(self) -> None:
        r = _make_oral_result(lambda_z=None, half_life=None, lambda_z_method=None)
        s = r.summary()
        assert "N/A" in s

    def test_with_warnings(self) -> None:
        r = _make_oral_result(warnings=["Only 3 points in terminal phase"])
        s = r.summary()
        assert "Warnings" in s
        assert "3 points" in s

    def test_no_warnings_section_when_empty(self) -> None:
        r = _make_oral_result(warnings=[])
        s = r.summary()
        assert "Warnings" not in s

    def test_shows_quality_metrics_when_present(self) -> None:
        r = _make_oral_result(lambda_z_adj_r2=0.998, lambda_z_n_points=4)
        s = r.summary()
        assert "adj_R2" in s
        assert "n points" in s

    def test_shows_steady_state_when_present(self) -> None:
        r = _make_oral_result(
            Cmax_ss=12.0,
            Cmin_ss=4.0,
            Cavg_ss=8.0,
            AUCtau=96.0,
            fluctuation_pct=100.0,
            swing=2.0,
            accumulation_ratio=1.5,
        )
        s = r.summary()
        assert "Steady-State" in s
        assert "Cmax_ss" in s
        assert "Accumulation" in s

    def test_shows_urinary_when_present(self) -> None:
        r = _make_oral_result(Ae=45.0, Ae_pct=45.0, CLr=0.9)
        s = r.summary()
        assert "Urinary" in s
        assert "Ae" in s
        assert "CLr" in s

    def test_degenerate_zeroes_dont_crash(self) -> None:
        r = NCAResult(
            subject="0",
            route="iv_bolus",
            dose=0.0,
            auc_method="linear",
            blq_method="zero",
            AUClast=0.0,
            AUCinf_obs=None,
            AUC_percent_extrapolated=None,
            Cmax=0.0,
            Tmax=0.0,
            lambda_z=None,
            half_life=None,
            lambda_z_method=None,
            CL=None,
            Vz=None,
        )
        s = r.summary()
        assert isinstance(s, str)


# ---------------------------------------------------------------------------
# NCASummaryResults
# ---------------------------------------------------------------------------


class TestNCASummaryResultsToDataFrame:
    """Tests for NCASummaryResults.to_dataframe().

    Expected: one row per subject with all NCAResult fields as columns.
    """

    def test_returns_dataframe(self) -> None:
        summary = NCASummaryResults(results=[_make_oral_result()])
        df = summary.to_dataframe()
        assert isinstance(df, pd.DataFrame)

    def test_one_row_per_subject(self) -> None:
        results = [_make_oral_result(subject="S1"), _make_oral_result(subject="S2")]
        df = NCASummaryResults(results=results).to_dataframe()
        assert len(df) == 2

    def test_subject_column(self) -> None:
        results = [_make_oral_result(subject="XYZ")]
        df = NCASummaryResults(results=results).to_dataframe()
        assert df["subject"].iloc[0] == "XYZ"

    def test_numeric_columns_float_type(self) -> None:
        results = [_make_oral_result()]
        df = NCASummaryResults(results=results).to_dataframe()
        assert df["AUClast"].dtype == float

    def test_empty_results_yields_empty_df(self) -> None:
        df = NCASummaryResults(results=[]).to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0


class TestNCASummaryResultsToCdiscPP:
    """Tests for NCASummaryResults.to_cdisc_pp().

    Reference: CDISC SDTM Implementation Guide v3.4 (PP domain).
    """

    def test_returns_dataframe(self) -> None:
        results = [_make_oral_result()]
        df = NCASummaryResults(results=results).to_cdisc_pp()
        assert isinstance(df, pd.DataFrame)

    def test_expected_columns(self) -> None:
        results = [_make_oral_result()]
        df = NCASummaryResults(results=results).to_cdisc_pp()
        expected = {
            "USUBJID",
            "PPTESTCD",
            "PPTEST",
            "PPORRES",
            "PPORRESU",
            "PPSTRESU",
            "PPSPEC",
            "PPDTC",
            "VISITNUM",
        }
        assert set(df.columns) == expected

    def test_pptestcd_values_are_cdisc_codes(self) -> None:
        results = [_make_oral_result()]
        df = NCASummaryResults(results=results).to_cdisc_pp()
        expected_codes = {"AUCLST", "AUCIFO", "AUCPEP", "CMAX", "TMAX", "LAMZ", "LAMZHL"}
        actual_codes = set(df["PPTESTCD"].unique())
        assert actual_codes == expected_codes

    def test_ppspec_is_plasma(self) -> None:
        results = [_make_oral_result()]
        df = NCASummaryResults(results=results).to_cdisc_pp()
        assert (df["PPSPEC"] == "PLASMA").all()

    def test_visitnum_is_one(self) -> None:
        results = [_make_oral_result()]
        df = NCASummaryResults(results=results).to_cdisc_pp()
        assert (df["VISITNUM"] == 1).all()

    def test_multiple_subjects_merge(self) -> None:
        results = [_make_oral_result(subject="S1"), _make_oral_result(subject="S2")]
        df = NCASummaryResults(results=results).to_cdisc_pp()
        assert set(df["USUBJID"].unique()) == {"S1", "S2"}
        assert len(df) == 14

    def test_auclast_value_in_pporres(self) -> None:
        results = [_make_oral_result(AUClast=95.0)]
        df = NCASummaryResults(results=results).to_cdisc_pp()
        auc_row = df[df["PPTESTCD"] == "AUCLST"]
        assert "95" in auc_row["PPORRES"].iloc[0]

    def test_none_params_are_skipped(self) -> None:
        r = _make_oral_result(
            lambda_z=None, half_life=None, AUCinf_obs=None, AUC_percent_extrapolated=None
        )
        df = NCASummaryResults(results=[r]).to_cdisc_pp()
        assert len(df) == 7

    def test_empty_results_yields_empty_df(self) -> None:
        df = NCASummaryResults(results=[]).to_cdisc_pp()
        assert len(df) == 0


class TestNCASummaryResultsSummary:
    """Tests for NCASummaryResults.summary()."""

    def test_returns_string(self) -> None:
        results = [_make_oral_result()]
        s = NCASummaryResults(results=results).summary()
        assert isinstance(s, str)

    def test_contains_subject(self) -> None:
        results = [_make_oral_result(subject="S42")]
        s = NCASummaryResults(results=results).summary()
        assert "S42" in s

    def test_contains_header_columns(self) -> None:
        results = [_make_oral_result()]
        s = NCASummaryResults(results=results).summary()
        assert "AUClast" in s
        assert "Cmax" in s
        assert "CL/CL_F" in s

    def test_ascii_safe(self) -> None:
        results = [_make_oral_result()]
        NCASummaryResults(results=results).summary().encode("ascii")

    def test_study_label_in_output(self) -> None:
        results = [_make_oral_result()]
        s = NCASummaryResults(results=results, study_label="My Study").summary()
        assert "My Study" in s

    def test_no_study_label_not_shown(self) -> None:
        results = [_make_oral_result()]
        s = NCASummaryResults(results=results, study_label="").summary()
        assert "Study:" not in s

    def test_multiple_subjects_tabulated(self) -> None:
        results = [_make_oral_result(subject="A"), _make_oral_result(subject="B")]
        s = NCASummaryResults(results=results).summary()
        assert "A" in s
        assert "B" in s


class TestNCASummaryResultsReport:
    """Tests for NCASummaryResults.report() convenience method."""

    def test_report_html(self, tmp_path: Path) -> None:
        results = [_make_oral_result()]
        summary = NCASummaryResults(results=results)
        out = tmp_path / "summary.html"
        content = summary.report(out, format="html")
        assert isinstance(content, str)
        assert out.exists()
        assert "OpenPKFlow" in content

    def test_report_markdown(self, tmp_path: Path) -> None:
        results = [_make_oral_result()]
        summary = NCASummaryResults(results=results)
        out = tmp_path / "summary.md"
        content = summary.report(out, format="markdown")
        assert isinstance(content, str)
        assert out.exists()
        assert "OpenPKFlow" in content

    def test_report_unknown_format_raises(self, tmp_path: Path) -> None:
        results = [_make_oral_result()]
        summary = NCASummaryResults(results=results)
        with pytest.raises(ValueError, match="Unknown format"):
            summary.report(tmp_path / "r.txt", format="txt")
