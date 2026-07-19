"""Tests for the FDA RSABE validation gate."""

from __future__ import annotations

import pandas as pd

from openpkflow.be import fda_partial_replicate_rsabe


def test_partial_replicate_rsabe_fails_closed_until_validated() -> None:
    data = pd.DataFrame({"sequence": ["TRR", "RTR", "RRT"], "Cmax": [1.0, 1.1, 0.9]})
    result = fda_partial_replicate_rsabe(data, value_col="Cmax")
    assert result.decision == "NOT_EVALUABLE"
    assert result.validation_status == "EXTERNAL_REFERENCE_REQUIRED"
