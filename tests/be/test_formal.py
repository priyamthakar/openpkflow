"""Tests for formal complete balanced 2x2 crossover ANOVA.

References
----------
FDA (2001) Statistical Approaches to Establishing Bioequivalence.
Jones B, Kenward MG (2014) Design and Analysis of Cross-Over Trials.
"""

from __future__ import annotations

import math

import pandas as pd
import pytest

from openpkflow.be import formal_be_anova


def _balanced_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "subject": ["S1", "S1", "S2", "S2", "S3", "S3", "S4", "S4"],
            "sequence": ["TR", "TR", "TR", "TR", "RT", "RT", "RT", "RT"],
            "period": [1, 2, 1, 2, 1, 2, 1, 2],
            "treatment": ["T", "R", "T", "R", "R", "T", "R", "T"],
            "AUCinf": [110.0, 100.0, 121.0, 110.0, 100.0, 110.0, 90.0, 99.0],
        }
    )


def test_identical_profiles_have_gmr_one_and_pass() -> None:
    data = _balanced_data()
    data["AUCinf"] = 100.0
    result = formal_be_anova(data, parameter="AUCinf")
    assert result.gmr == pytest.approx(1.0)
    assert result.decision == "PASS"
    assert result.cv_intra_pct == pytest.approx(0.0)


def test_formal_anova_has_expected_treatment_contrast() -> None:
    result = formal_be_anova(_balanced_data(), parameter="AUCinf")
    expected = math.log(1.1)
    assert result.treatment_difference == pytest.approx(expected, abs=0.015)
    assert result.gmr == pytest.approx(1.1, abs=0.02)
    assert result.residual_df == 2
    assert result.decision == "PASS"
    assert [row.source for row in result.anova] == [
        "Sequence",
        "Subject within sequence",
        "Period",
        "Treatment",
        "Residual",
    ]


def test_sequence_uses_subject_within_sequence_denominator() -> None:
    result = formal_be_anova(_balanced_data(), parameter="AUCinf")
    sequence, subject_within, _period, _treatment, residual = result.anova
    assert sequence.f_value == pytest.approx(sequence.mean_square / subject_within.mean_square)
    assert subject_within.f_value == pytest.approx(
        subject_within.mean_square / residual.mean_square
    )


@pytest.mark.parametrize(
    "mutator",
    [
        lambda data: data.drop(index=0),
        lambda data: data.assign(sequence=["TR"] * len(data)),
        lambda data: pd.concat([data, data.iloc[[0]]], ignore_index=True),
        lambda data: data.assign(AUCinf=-1.0),
    ],
)
def test_invalid_formal_design_fails_closed(mutator) -> None:
    with pytest.raises(ValueError):
        formal_be_anova(mutator(_balanced_data()), parameter="AUCinf")


def test_unbalanced_sequence_allocation_fails_closed() -> None:
    data = pd.concat(
        [
            _balanced_data(),
            pd.DataFrame(
                {
                    "subject": ["S5", "S5"],
                    "sequence": ["TR", "TR"],
                    "period": [1, 2],
                    "treatment": ["T", "R"],
                    "AUCinf": [110.0, 100.0],
                }
            ),
        ],
        ignore_index=True,
    )
    with pytest.raises(ValueError, match="balanced"):
        formal_be_anova(data, parameter="AUCinf")


def test_formal_report_includes_anova(tmp_path) -> None:
    result = formal_be_anova(_balanced_data(), parameter="AUCinf")
    output = tmp_path / "formal_be.html"
    result.report(output)
    assert "ANOVA Table" in output.read_text(encoding="utf-8")
