"""Tests for steady-state NCA and urinary excretion parameters.

References
----------
Rowland, M., & Tozer, T. N. (2011). Clinical Pharmacokinetics and
Pharmacodynamics: Concepts and Applications (4th ed.). Lippincott Williams & Wilkins.

FDA Guidance for Industry: Pharmacokinetic Studies in Man (1988). CDER.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from openpkflow.nca.methods import (
    accumulation_ratio,
    auc_tau,
    cumulative_urinary_excretion,
    percent_excreted,
    renal_clearance,
    steady_state_parameters,
)
from openpkflow.nca.study import NCAStudy

# ---------------------------------------------------------------------------
# auc_tau
# ---------------------------------------------------------------------------


class TestAUCTau:
    def test_simple_linear(self) -> None:
        t = [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0]
        c = [0.0, 10.0, 15.0, 12.0, 8.0, 5.0, 3.0]
        result = auc_tau(t, c, tau=12.0, method="linear")
        assert result > 0
        assert result == pytest.approx(91.0, rel=0.2)

    def test_tau_must_be_positive(self) -> None:
        with pytest.raises(ValueError, match="tau must be positive"):
            auc_tau([0.0, 1.0], [1.0, 2.0], tau=0.0)

    def test_negative_tau_raises(self) -> None:
        with pytest.raises(ValueError, match="tau must be positive"):
            auc_tau([0.0, 1.0], [1.0, 2.0], tau=-1.0)


# ---------------------------------------------------------------------------
# steady_state_parameters
# ---------------------------------------------------------------------------


class TestSteadyStateParameters:
    def test_full_parameters(self) -> None:
        t = [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0]
        c = [3.0, 12.0, 15.0, 11.0, 8.0, 5.5, 3.5]
        result = steady_state_parameters(t, c, tau=12.0)
        assert result["Cmax_ss"] == 15.0
        assert result["Cmin_ss"] == 3.0
        assert result["AUCtau"] > 0
        assert result["Cavg_ss"] > 0
        assert result["fluctuation_pct"] is not None
        assert result["fluctuation_pct"] > 0
        assert result["swing"] is not None
        assert result["swing"] > 0
        assert result["accumulation_ratio"] is None

    def test_zero_cmin_handled(self) -> None:
        t = [0.0, 2.0, 4.0, 6.0]
        c = [0.0, 10.0, 5.0, 0.0]
        result = steady_state_parameters(t, c, tau=6.0)
        assert result["Cmin_ss"] == 0.0
        assert result["swing"] is None


# ---------------------------------------------------------------------------
# accumulation_ratio
# ---------------------------------------------------------------------------


class TestAccumulationRatio:
    def test_ratio_greater_than_one(self) -> None:
        r = accumulation_ratio(200.0, 100.0)
        assert r == 2.0

    def test_no_accumulation(self) -> None:
        r = accumulation_ratio(100.0, 100.0)
        assert r == 1.0

    def test_sd_auc_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="auctau_sd must be positive"):
            accumulation_ratio(100.0, 0.0)


# ---------------------------------------------------------------------------
# cumulative_urinary_excretion
# ---------------------------------------------------------------------------


class TestCumulativeUrinaryExcretion:
    def test_simple_linear_excretion(self) -> None:
        t = [1.0, 3.0, 5.0, 7.0]
        vol = [100.0, 150.0, 120.0, 100.0]
        conc = [0.5, 1.0, 0.8, 0.3]
        result = cumulative_urinary_excretion(t, vol, conc)
        expected = np.array([50.0, 200.0, 296.0, 326.0])
        assert np.allclose(result, expected)

    def test_all_zero_excretion(self) -> None:
        result = cumulative_urinary_excretion([1.0, 2.0], [100.0, 100.0], [0.0, 0.0])
        assert np.all(result == 0.0)

    def test_mismatched_lengths_raises(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            cumulative_urinary_excretion([1.0, 2.0], [100.0], [0.5, 1.0])

    def test_negative_volume_raises(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            cumulative_urinary_excretion([1.0, 2.0], [-1.0, 100.0], [0.5, 0.5])

    def test_negative_conc_raises(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            cumulative_urinary_excretion([1.0, 2.0], [100.0, 100.0], [0.5, -0.1])


# ---------------------------------------------------------------------------
# renal_clearance
# ---------------------------------------------------------------------------


class TestRenalClearance:
    def test_computed_correctly(self) -> None:
        clr = renal_clearance(500.0, 2500.0)
        assert clr == 0.2

    def test_zero_auc_raises(self) -> None:
        with pytest.raises(ValueError, match="auc_inf must be positive"):
            renal_clearance(100.0, 0.0)

    def test_negative_ae_raises(self) -> None:
        with pytest.raises(ValueError, match="total_ae must be >= 0"):
            renal_clearance(-10.0, 100.0)


# ---------------------------------------------------------------------------
# percent_excreted
# ---------------------------------------------------------------------------


class TestPercentExcreted:
    def test_computed_correctly(self) -> None:
        pct = percent_excreted(250.0, 500.0)
        assert pct == 50.0

    def test_zero_dose_raises(self) -> None:
        with pytest.raises(ValueError, match="dose must be positive"):
            percent_excreted(100.0, 0.0)

    def test_negative_ae_raises(self) -> None:
        with pytest.raises(ValueError, match="total_ae must be >= 0"):
            percent_excreted(-10.0, 500.0)


# ---------------------------------------------------------------------------
# NCAStudy integration tests
# ---------------------------------------------------------------------------


class TestNCAStudySteadyState:
    def test_steady_state_params_present(self) -> None:
        df = pd.DataFrame(
            {
                "subject": ["S1"] * 8,
                "time": [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 24.0],
                "conc": [3.0, 12.0, 15.0, 11.0, 8.0, 5.5, 3.5, 1.0],
                "dose": [100.0] * 8,
                "route": ["oral"] * 8,
            }
        )
        study = NCAStudy(
            df,
            auc_method="linear_up_log_down",
            blq_method="none",
            steady_state=True,
            tau=12.0,
        )
        summary = study.analyze()
        r = summary.results[0]
        assert r.Cmax_ss is not None
        assert r.Cmax_ss == 15.0
        assert r.Cmin_ss is not None
        assert r.AUCtau is not None
        assert r.fluctuation_pct is not None
        assert r.fluctuation_pct > 0

    def test_steady_state_without_tau_raises(self) -> None:
        df = pd.DataFrame(
            {
                "subject": ["S1"] * 3,
                "time": [0.0, 1.0, 2.0],
                "conc": [1.0, 2.0, 3.0],
                "dose": [100.0] * 3,
                "route": ["oral"] * 3,
            }
        )
        with pytest.raises(ValueError, match="tau is required"):
            NCAStudy(
                df,
                auc_method="linear",
                blq_method="none",
                steady_state=True,
            )

    def test_non_ss_study_has_none_ss_fields(self) -> None:
        df = pd.DataFrame(
            {
                "subject": ["S1"] * 4,
                "time": [0.0, 1.0, 2.0, 3.0],
                "conc": [0.0, 5.0, 3.0, 2.0],
                "dose": [100.0] * 4,
                "route": ["oral"] * 4,
            }
        )
        study = NCAStudy(df, auc_method="linear", blq_method="none")
        summary = study.analyze()
        r = summary.results[0]
        assert r.Cmax_ss is None
        assert r.AUCtau is None
        assert r.fluctuation_pct is None


class TestNCAStudyUrinaryExcretion:
    def test_urine_params_present(self) -> None:
        df = pd.DataFrame(
            {
                "subject": ["S1"] * 4,
                "time": [0.0, 1.0, 2.0, 3.0],
                "conc": [0.0, 5.0, 3.0, 2.0],
                "dose": [200.0] * 4,
                "route": ["oral"] * 4,
                "urine_vol": [100.0, 150.0, 120.0, 80.0],
                "urine_conc": [0.1, 0.5, 0.3, 0.1],
            }
        )
        study = NCAStudy(
            df,
            auc_method="linear",
            blq_method="none",
            urine_volume_col="urine_vol",
            urine_conc_col="urine_conc",
        )
        summary = study.analyze()
        r = summary.results[0]
        assert r.Ae is not None
        assert r.Ae > 0
        assert r.Ae_pct is not None
        assert r.Ae_pct > 0

    def test_no_urine_cols_leaves_none(self) -> None:
        df = pd.DataFrame(
            {
                "subject": ["S1"] * 4,
                "time": [0.0, 1.0, 2.0, 3.0],
                "conc": [0.0, 5.0, 3.0, 2.0],
                "dose": [200.0] * 4,
                "route": ["oral"] * 4,
            }
        )
        study = NCAStudy(df, auc_method="linear", blq_method="none")
        summary = study.analyze()
        r = summary.results[0]
        assert r.Ae is None
        assert r.Ae_pct is None
        assert r.CLr is None

    def test_to_dict_includes_new_fields(self) -> None:
        df = pd.DataFrame(
            {
                "subject": ["S1"] * 4,
                "time": [0.0, 1.0, 2.0, 3.0],
                "conc": [0.0, 5.0, 3.0, 2.0],
                "dose": [200.0] * 4,
                "route": ["oral"] * 4,
            }
        )
        study = NCAStudy(df, auc_method="linear", blq_method="none", steady_state=True, tau=4.0)
        summary = study.analyze()
        d = summary.results[0].to_dict()
        assert "Cmax_ss" in d
        assert "AUCtau" in d
        assert "Ae" in d
        assert "CLr" in d


class TestNCAStudyCdiscPP:
    def test_to_cdisc_pp_still_works(self) -> None:
        df = pd.DataFrame(
            {
                "subject": ["S1"] * 4,
                "time": [0.0, 1.0, 2.0, 3.0],
                "conc": [0.0, 5.0, 3.0, 2.0],
                "dose": [200.0] * 4,
                "route": ["oral"] * 4,
            }
        )
        study = NCAStudy(df, auc_method="linear", blq_method="none")
        summary = study.analyze()
        pp = summary.to_cdisc_pp()
        assert len(pp) > 0
        assert "USUBJID" in pp.columns
        assert "PPTESTCD" in pp.columns
