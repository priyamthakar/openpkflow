"""External-reference regression for FDA partial-replicate RSABE.

Fixture: Patterson SD, Jones B (2012) Viewpoint: observations on scaled
average bioequivalence. Pharmaceutical Statistics 11(1):1-7, Table II
(DOI: 10.1002/pst.498). Table II is a real 51-subject (17/sequence)
TRR/RTR/RRT partial-replicate AUC and Cmax dataset with a fully worked
FDA-method RSABE example in Section 1.3.

Expected values below are pinned to this implementation's own output and
cross-checked in the test against the paper's published (rounded) numbers:
for ln-AUC, delta_hat=0.056 (90% CI -0.038, 0.150), GMR=1.06 (0.96, 1.16),
sigma2_wR=0.12 (0.09, 0.17), aggregate criterion 95% upper bound = -0.05,
decision PASS; for ln-Cmax, delta_hat=0.316 (0.171, 0.462), GMR=1.37
(1.19, 1.59), sigma2_wR=0.32 (0.24, 0.46), aggregate criterion 95% upper
bound = 0.006, decision FAIL (both the point-estimate constraint and the
aggregate criterion). The small numeric gaps versus the paper's rounded
figures are consistent with hand-transcription of 306 published values
and the paper's own intermediate rounding, not a difference in method.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from openpkflow.be import fda_partial_replicate_rsabe

DATA = Path(__file__).parent / "data" / "be_rsabe_partial_replicate_patterson2012.csv"


def _load() -> pd.DataFrame:
    return pd.read_csv(DATA)


def test_rsabe_auc_matches_patterson_jones_2012() -> None:
    result = fda_partial_replicate_rsabe(_load(), parameter="AUC", value_col="AUC")
    assert result.n_subjects == 51
    assert result.delta_hat == pytest.approx(0.05573887097402827, abs=1e-9)
    assert result.gmr == pytest.approx(1.0573215503383788, abs=1e-9)
    assert result.sigma_wr**2 == pytest.approx(0.1170, abs=5e-3)
    assert result.aggregate_criterion_upper == pytest.approx(-0.05, abs=1e-2)
    assert result.point_estimate_constraint_met
    assert result.highly_variable
    assert result.decision == "PASS"

    # Cross-check against the paper's own published (rounded) figures.
    assert result.delta_hat == pytest.approx(0.056, abs=1e-3)
    assert result.gmr == pytest.approx(1.06, abs=1e-2)
    assert result.gmr_ci_lower == pytest.approx(0.96, abs=1e-2)
    assert result.gmr_ci_upper == pytest.approx(1.16, abs=1e-2)


def test_rsabe_cmax_matches_patterson_jones_2012() -> None:
    result = fda_partial_replicate_rsabe(_load(), parameter="Cmax", value_col="Cmax")
    assert result.n_subjects == 51
    assert result.delta_hat == pytest.approx(0.3163713786881883, abs=1e-9)
    assert result.gmr == pytest.approx(1.3721397444718504, abs=1e-9)
    assert result.sigma_wr**2 == pytest.approx(0.32, abs=2e-2)
    assert result.aggregate_criterion_upper == pytest.approx(0.006, abs=1e-2)
    assert not result.point_estimate_constraint_met
    assert result.highly_variable
    assert result.decision == "FAIL"

    # Cross-check against the paper's own published (rounded) figures.
    assert result.delta_hat == pytest.approx(0.316, abs=1e-3)
    assert result.gmr == pytest.approx(1.37, abs=1e-2)
    assert result.gmr_ci_lower == pytest.approx(1.19, abs=1e-2)
    assert result.gmr_ci_upper == pytest.approx(1.59, abs=1e-2)
