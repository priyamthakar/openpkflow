"""Reference validation tests for NCA against the R nlme Theoph dataset.

Values are verified against our own NCA implementation and checked against
published theophylline pharmacokinetic reference ranges.

Reference data source:
  Pinheiro JC, Bates DM (2000). Mixed-effects models in S and S-PLUS.
  Springer, New York. (R nlme::Theoph dataset)

Pharmacological reference ranges (healthy adult oral theophylline):
  - Half-life: 6-12 h (literature; may extend to ~14 h in some subjects)
  - Cmax: ~5-12 mg/L at therapeutic doses
  - AUClast (0-24h, ~320 mg dose): ~70-150 h*mg/L

All computations use auc_method="linear_up_log_down", blq_method="none".
Regression assertions use ±1% tolerance (self-consistency check).
"""

from __future__ import annotations

import pytest

from openpkflow.datasets import example_theoph_path
from openpkflow.nca.study import NCAStudy


@pytest.fixture(scope="module")
def theoph_summary():
    """Run NCA on the Theoph dataset once per test module."""
    study = NCAStudy.from_csv(
        example_theoph_path(),
        auc_method="linear_up_log_down",
        blq_method="none",
    )
    return study.analyze()


class TestTheophStructure:
    def test_twelve_subjects_present(self, theoph_summary) -> None:
        assert len(theoph_summary.results) == 12

    def test_all_subjects_have_positive_auclast(self, theoph_summary) -> None:
        for r in theoph_summary.results:
            assert r.AUClast > 0, f"Subject {r.subject} has non-positive AUClast"

    def test_all_subjects_have_positive_cmax(self, theoph_summary) -> None:
        for r in theoph_summary.results:
            assert r.Cmax > 0, f"Subject {r.subject} has non-positive Cmax"

    def test_all_routes_are_oral(self, theoph_summary) -> None:
        for r in theoph_summary.results:
            assert r.route == "oral", f"Subject {r.subject} route={r.route!r}"

    def test_all_oral_subjects_have_clf(self, theoph_summary) -> None:
        # All subjects should converge on lambda_z (clean theophylline decline)
        no_clf = [r.subject for r in theoph_summary.results if r.CL_F is None]
        assert no_clf == [], f"Subjects missing CL_F: {no_clf}"


class TestTheophPhysiology:
    """Pharmacological plausibility checks — not tight regression."""

    def test_cmax_in_therapeutic_range(self, theoph_summary) -> None:
        # Theophylline Cmax at ~320 mg should be 5-12 mg/L
        for r in theoph_summary.results:
            assert 4.0 < r.Cmax < 15.0, f"Subject {r.subject} Cmax={r.Cmax} out of range"

    def test_half_life_in_expected_range(self, theoph_summary) -> None:
        # Theophylline t1/2 is typically 6-14 h (up to 15h in slow metabolisers)
        for r in theoph_summary.results:
            if r.half_life is not None:
                assert 4.0 < r.half_life < 18.0, (
                    f"Subject {r.subject} half_life={r.half_life:.2f} out of range"
                )

    def test_auclast_in_plausible_range(self, theoph_summary) -> None:
        # 0-24h AUClast at ~320 mg dose should be between 50 and 200 h*mg/L
        for r in theoph_summary.results:
            assert 50.0 < r.AUClast < 200.0, (
                f"Subject {r.subject} AUClast={r.AUClast:.1f} out of range"
            )

    def test_tmax_before_peak_then_decline(self, theoph_summary) -> None:
        # Oral absorption: Tmax should be < 5 h for theophylline
        for r in theoph_summary.results:
            assert r.Tmax < 6.0, f"Subject {r.subject} Tmax={r.Tmax} unexpectedly late"


class TestTheophRegression:
    """Self-consistent regression tests — assert the implementation produces
    stable results (tolerance ±1%). Do not change these values without re-running
    the analysis and documenting why the numbers changed.

    Computed with openpkflow NCA, auc_method=linear_up_log_down, blq_method=none,
    on the embedded datasets/theoph.csv (R nlme::Theoph, doses precomputed in mg).
    """

    def test_mean_auclast_regression(self, theoph_summary) -> None:
        df = theoph_summary.to_dataframe()
        assert df["AUClast"].mean() == pytest.approx(98.52, rel=0.01)

    def test_mean_cmax_regression(self, theoph_summary) -> None:
        df = theoph_summary.to_dataframe()
        assert df["Cmax"].mean() == pytest.approx(8.89, rel=0.01)

    def test_mean_half_life_regression(self, theoph_summary) -> None:
        df = theoph_summary.to_dataframe()
        assert df["half_life"].dropna().mean() == pytest.approx(7.89, rel=0.01)

    def test_mean_aucinf_obs_regression(self, theoph_summary) -> None:
        df = theoph_summary.to_dataframe()
        assert df["AUCinf_obs"].dropna().mean() == pytest.approx(117.78, rel=0.01)


class TestTheophSubject1:
    """Spot-check Subject 1 against directly readable values in the CSV."""

    def test_subject1_cmax(self, theoph_summary) -> None:
        r = next(r for r in theoph_summary.results if r.subject == "1")
        # Cmax is directly observed: 10.50 mg/L at t=1.12 h
        assert r.Cmax == pytest.approx(10.50, rel=0.001)

    def test_subject1_tmax(self, theoph_summary) -> None:
        r = next(r for r in theoph_summary.results if r.subject == "1")
        # Tmax is directly observed: 1.12 h
        assert r.Tmax == pytest.approx(1.12, rel=0.001)

    def test_subject1_half_life_in_range(self, theoph_summary) -> None:
        r = next(r for r in theoph_summary.results if r.subject == "1")
        if r.half_life is not None:
            assert 4.0 < r.half_life < 20.0

    def test_subject1_clf_positive(self, theoph_summary) -> None:
        r = next(r for r in theoph_summary.results if r.subject == "1")
        if r.CL_F is not None:
            assert r.CL_F > 0
