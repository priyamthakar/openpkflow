"""External-reference regression for complete balanced 2x2 formal BE ANOVA.

The expected treatment contrast and residual MSE were generated with the
independent R model in ``scripts/be_anova_crossval.R`` using R 4.6.0.

References
----------
FDA (2001) Statistical Approaches to Establishing Bioequivalence.
Jones B, Kenward MG (2014) Design and Analysis of Cross-Over Trials.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from openpkflow.be import formal_be_anova

DATA = Path(__file__).parent / "data" / "be_anova_balanced_2x2.csv"


def test_formal_anova_matches_independent_r_reference() -> None:
    result = formal_be_anova(pd.read_csv(DATA), parameter="AUCinf")
    assert result.treatment_difference == pytest.approx(0.095931482001, abs=1e-10)
    assert result.gmr == pytest.approx(1.100683644769, abs=1e-10)
    assert result.residual_mse == pytest.approx(0.000183925324, abs=1e-12)
    assert result.decision == "PASS"
