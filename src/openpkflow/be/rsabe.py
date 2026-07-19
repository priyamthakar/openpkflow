"""FDA partial-replicate RSABE validation gate.

This module intentionally does not calculate a formal FDA RSABE decision until
the partial-replicate model has pinned independent reference fixtures.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd


@dataclass(frozen=True)
class FdaRsabeResult:
    """Validation-gated FDA partial-replicate RSABE result."""

    decision: Literal["NOT_EVALUABLE"]
    design: str
    jurisdiction: Literal["FDA"]
    validation_status: Literal["EXTERNAL_REFERENCE_REQUIRED"]
    message: str


def fda_partial_replicate_rsabe(
    data: pd.DataFrame,
    *,
    value_col: str,
    sequence_col: str = "sequence",
) -> FdaRsabeResult:
    """Return NOT_EVALUABLE until FDA RSABE external validation is complete.

    Parameters
    ----------
    data : pd.DataFrame
        Partial-replicate long-format data.
    value_col : str
        Positive PK endpoint column required by the future formal model.
    sequence_col : str, optional
        Sequence column expected to contain TRR, RTR, and RRT.

    Returns
    -------
    FdaRsabeResult
        Explicitly non-decisional validation-gate result.
    """
    if value_col not in data.columns or sequence_col not in data.columns:
        raise ValueError("RSABE input must contain endpoint and sequence columns.")
    sequences = {str(value).upper() for value in data[sequence_col].dropna()}
    if not sequences.issubset({"TRR", "RTR", "RRT"}):
        raise ValueError("FDA initial RSABE scope supports only TRR/RTR/RRT sequences.")
    return FdaRsabeResult(
        decision="NOT_EVALUABLE",
        design="partial_replicate_2x2x3",
        jurisdiction="FDA",
        validation_status="EXTERNAL_REFERENCE_REQUIRED",
        message=(
            "FDA partial-replicate RSABE is not evaluable until the OpenPKFlow "
            "external-reference validation gate for model fitting and upper confidence "
            "bound parity is satisfied."
        ),
    )
