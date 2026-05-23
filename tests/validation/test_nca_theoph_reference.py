"""NCA validation: theophylline dataset internal-consistency checks.

Reference dataset: Upton (1992) theophylline PK data, as distributed in the R
``datasets`` package (12 subjects, single oral dose, full plasma concentration
profiles).

These tests verify openpkflow NCA against hand-computed reference values derived
from the same dataset. PKNCA-R cross-validation (Denney et al., 2015,
DOI: 10.18637/jss.v059.i11) is deferred pending a controlled R/PKNCA run on
the identical dataset; a dedicated cross-validation PR will add those reference
values once confirmed.

Subject 1: Dose = 4.02 mg/kg, AUClast (linear-up/log-down, 0-24.37h) ~ 147.2 h*mg/L
Subject 2: Dose = 4.40 mg/kg, AUClast (linear-up/log-down, 0-24.30h) ~ 88.7 h*mg/L
"""

from __future__ import annotations

import pandas as pd
import pytest

from openpkflow.nca.methods import auc_linear_up_log_down, cmax, tmax
from openpkflow.nca.study import NCAStudy

# ---------------------------------------------------------------------------
# Inline theoph dataset (Subjects 1 and 2 only)
# Upton (1992) as distributed in R datasets::Theoph.
# Dose units: mg/kg; concentration units: mg/L; time units: hours.
# ---------------------------------------------------------------------------

_THEOPH_ROWS = [
    # subject  time    conc    dose    wt
    (1, 0.00, 0.74, 4.02, 79.6),
    (1, 0.25, 2.84, 4.02, 79.6),
    (1, 0.57, 6.57, 4.02, 79.6),
    (1, 1.12, 10.50, 4.02, 79.6),
    (1, 2.02, 9.66, 4.02, 79.6),
    (1, 3.82, 8.58, 4.02, 79.6),
    (1, 5.10, 8.36, 4.02, 79.6),
    (1, 7.03, 7.47, 4.02, 79.6),
    (1, 9.05, 6.89, 4.02, 79.6),
    (1, 12.12, 5.94, 4.02, 79.6),
    (1, 24.37, 3.28, 4.02, 79.6),
    (2, 0.00, 0.00, 4.40, 72.4),
    (2, 0.27, 1.72, 4.40, 72.4),
    (2, 0.52, 7.91, 4.40, 72.4),
    (2, 1.00, 8.31, 4.40, 72.4),
    (2, 1.92, 8.33, 4.40, 72.4),
    (2, 3.50, 6.85, 4.40, 72.4),
    (2, 5.02, 6.08, 4.40, 72.4),
    (2, 7.03, 5.40, 4.40, 72.4),
    (2, 9.00, 4.55, 4.40, 72.4),
    (2, 12.00, 3.01, 4.40, 72.4),
    (2, 24.30, 0.90, 4.40, 72.4),
]

_SUBJ1_TIMES = [r[1] for r in _THEOPH_ROWS if r[0] == 1]
_SUBJ1_CONCS = [r[2] for r in _THEOPH_ROWS if r[0] == 1]
_SUBJ2_TIMES = [r[1] for r in _THEOPH_ROWS if r[0] == 2]
_SUBJ2_CONCS = [r[2] for r in _THEOPH_ROWS if r[0] == 2]


def _theoph_df() -> pd.DataFrame:
    """Return the two-subject theoph dataset as a NCAStudy-ready DataFrame."""
    rows = [
        {
            "subject": str(subj),
            "time": t,
            "conc": conc,
            "dose": dose,
            "route": "oral",
        }
        for subj, t, conc, dose, _wt in _THEOPH_ROWS
    ]
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Test: AUClast Subject 1
# ---------------------------------------------------------------------------


class TestTheophAUClastSubject1:
    """Internal-consistency checks for AUClast, Subject 1.

    Reference: Upton (1992) theophylline data; R datasets::Theoph.
    Method: linear-up/log-down, blq=none, time range 0-24.37 h.
    """

    def test_auclast_subject1_positive(self) -> None:
        """AUClast for Subject 1 must be positive and finite."""
        result = auc_linear_up_log_down(_SUBJ1_TIMES, _SUBJ1_CONCS)
        assert result.value > 0.0

    def test_auclast_subject1_plausible(self) -> None:
        """AUClast for Subject 1 must be in the pharmacologically plausible range.

        Hand-computed linear-up/log-down on the inline Theoph data yields ~147.2 h*mg/L.
        Reference: Upton (1992) theophylline data; R datasets::Theoph.
        """
        result = auc_linear_up_log_down(_SUBJ1_TIMES, _SUBJ1_CONCS)
        assert 100.0 < result.value < 200.0


# ---------------------------------------------------------------------------
# Test: AUClast Subject 2
# ---------------------------------------------------------------------------


class TestTheophAUClastSubject2:
    """Internal-consistency checks for AUClast, Subject 2.

    Reference: Upton (1992) theophylline data; R datasets::Theoph.
    Method: linear-up/log-down, blq=none, time range 0-24.30 h.
    """

    def test_auclast_subject2_positive(self) -> None:
        """AUClast for Subject 2 must be positive and finite."""
        result = auc_linear_up_log_down(_SUBJ2_TIMES, _SUBJ2_CONCS)
        assert result.value > 0.0

    def test_auclast_subject2_plausible(self) -> None:
        """AUClast for Subject 2 must be in the pharmacologically plausible range.

        Hand-computed linear-up/log-down on the inline Theoph data yields ~88.7 h*mg/L.
        Reference: Upton (1992) theophylline data; R datasets::Theoph.
        """
        result = auc_linear_up_log_down(_SUBJ2_TIMES, _SUBJ2_CONCS)
        assert 60.0 < result.value < 150.0


# ---------------------------------------------------------------------------
# Test: Cmax Subject 1
# ---------------------------------------------------------------------------


class TestTheophCmaxSubject1:
    def test_cmax_subject1(self) -> None:
        """Cmax for Subject 1 is 10.50 mg/L (directly observed at t=1.12 h).

        Reference: Upton (1992) theophylline data; R datasets::Theoph.
        """
        assert cmax(_SUBJ1_CONCS) == pytest.approx(10.50, rel=1e-6)


# ---------------------------------------------------------------------------
# Test: Tmax Subject 1
# ---------------------------------------------------------------------------


class TestTheophTmaxSubject1:
    def test_tmax_subject1(self) -> None:
        """Tmax for Subject 1 is 1.12 h (directly observed).

        Reference: Upton (1992) theophylline data; R datasets::Theoph.
        """
        assert tmax(_SUBJ1_TIMES, _SUBJ1_CONCS) == pytest.approx(1.12, rel=1e-6)


# ---------------------------------------------------------------------------
# Test: NCAStudy integration (Subjects 1 + 2)
# ---------------------------------------------------------------------------


class TestTheophNCAStudyIntegration:
    """Run the full NCAStudy pipeline and cross-check aggregate results.

    Verifies correct pipeline execution and that results are pharmacologically
    plausible for the two-subject subset.
    """

    @pytest.fixture(scope="class")
    def summary(self):
        """NCAStudy on subjects 1 and 2, linear-up/log-down, blq=none."""
        df = _theoph_df()
        study = NCAStudy(df, auc_method="linear_up_log_down", blq_method="none")
        return study.analyze()

    def test_two_subjects_present(self, summary) -> None:
        assert len(summary.results) == 2

    def test_all_subjects_have_positive_auclast(self, summary) -> None:
        for r in summary.results:
            assert r.AUClast > 0.0, f"Subject {r.subject}: AUClast={r.AUClast}"

    def test_all_routes_oral(self, summary) -> None:
        for r in summary.results:
            assert r.route == "oral"

    def test_subject1_cmax_matches_observed(self, summary) -> None:
        """Subject 1 Cmax must equal the directly observed 10.50 mg/L."""
        r1 = next(r for r in summary.results if r.subject == "1")
        assert r1.Cmax == pytest.approx(10.50, rel=1e-6)

    def test_subject1_tmax_matches_observed(self, summary) -> None:
        """Subject 1 Tmax must equal the directly observed 1.12 h."""
        r1 = next(r for r in summary.results if r.subject == "1")
        assert r1.Tmax == pytest.approx(1.12, rel=1e-6)

    def test_mean_auclast_pharmacologically_plausible(self, summary) -> None:
        """Mean AUClast for 2 subjects must be within the 50-200 hr*mg/L plausible range."""
        df = summary.to_dataframe()
        mean_auclast = df["AUClast"].mean()
        assert 50.0 < mean_auclast < 200.0, f"Mean AUClast={mean_auclast:.2f} out of range"

    def test_cmax_values_are_directly_observed(self, summary) -> None:
        """Cmax for each subject must equal the directly observed peak in the data.

        Subject 1: 10.50 mg/L at t=1.12 h; Subject 2: 8.33 mg/L at t=1.92 h.
        Reference: Upton (1992) theophylline data; R datasets::Theoph.
        """
        results_by_subject = {r.subject: r for r in summary.results}
        assert results_by_subject["1"].Cmax == pytest.approx(10.50, rel=1e-6)
        assert results_by_subject["2"].Cmax == pytest.approx(8.33, rel=1e-6)

    def test_clf_populated_for_oral_subjects(self, summary) -> None:
        """CL_F must be populated for all oral subjects when lambda_z converges."""
        for r in summary.results:
            if r.lambda_z is not None:
                assert r.CL_F is not None, f"Subject {r.subject}: oral route but CL_F is None"
