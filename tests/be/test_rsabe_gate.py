"""Tests for FDA partial-replicate RSABE fail-closed validation."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from openpkflow.be import fda_partial_replicate_rsabe


def _complete_design(n_per_sequence: int = 2, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    sequences = {"TRR": ("T", "R", "R"), "RTR": ("R", "T", "R"), "RRT": ("R", "R", "T")}
    subject = 1
    for sequence, treatments in sequences.items():
        for _ in range(n_per_sequence):
            base = rng.uniform(80.0, 120.0)
            for period, treatment in enumerate(treatments, start=1):
                rows.append(
                    {
                        "subject": subject,
                        "sequence": sequence,
                        "period": period,
                        "treatment": treatment,
                        "value": base * rng.uniform(0.7, 1.3),
                    }
                )
            subject += 1
    return pd.DataFrame(rows)


def test_partial_replicate_rsabe_requires_all_three_sequences() -> None:
    data = pd.DataFrame(
        {
            "subject": [1, 1, 1, 2, 2, 2],
            "sequence": ["TRR", "TRR", "TRR", "RTR", "RTR", "RTR"],
            "period": [1, 2, 3, 1, 2, 3],
            "treatment": ["T", "R", "R", "R", "T", "R"],
            "value": [1.0, 1.1, 0.9, 1.0, 1.1, 0.9],
        }
    )
    with pytest.raises(ValueError, match="TRR, RTR, and RRT"):
        fda_partial_replicate_rsabe(data, parameter="Cmax", value_col="value")


def test_partial_replicate_rsabe_requires_at_least_four_subjects() -> None:
    data = _complete_design(n_per_sequence=1)
    with pytest.raises(ValueError, match="at least four subjects"):
        fda_partial_replicate_rsabe(data, parameter="Cmax", value_col="value")


def test_partial_replicate_rsabe_requires_complete_three_period_subjects() -> None:
    data = _complete_design(n_per_sequence=2)
    incomplete = data.drop(index=0).reset_index(drop=True)
    with pytest.raises(ValueError, match="complete three-period"):
        fda_partial_replicate_rsabe(incomplete, parameter="Cmax", value_col="value")


def test_partial_replicate_rsabe_requires_treatment_matches_sequence() -> None:
    data = _complete_design(n_per_sequence=2)
    data.loc[0, "treatment"] = "R"
    with pytest.raises(ValueError, match="Treatment assignments"):
        fda_partial_replicate_rsabe(data, parameter="Cmax", value_col="value")


def test_partial_replicate_rsabe_rejects_non_positive_values() -> None:
    data = _complete_design(n_per_sequence=2)
    data.loc[0, "value"] = 0.0
    with pytest.raises(ValueError, match="must be > 0"):
        fda_partial_replicate_rsabe(data, parameter="Cmax", value_col="value")


def test_partial_replicate_rsabe_not_evaluable_when_not_highly_variable() -> None:
    rng = np.random.default_rng(1)
    data = _complete_design(n_per_sequence=6, seed=1)
    data["value"] = 100.0 + rng.normal(0, 1, len(data))
    result = fda_partial_replicate_rsabe(data, parameter="Cmax", value_col="value")
    assert result.decision == "NOT_EVALUABLE"
    assert result.validation_status == "VALIDATED"
    assert not result.highly_variable
