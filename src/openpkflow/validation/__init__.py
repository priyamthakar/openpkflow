"""Validation utilities -- reference comparisons and cross-tool checks."""

from __future__ import annotations


def pct_bias(observed: float, reference: float) -> float:
    """Compute percent bias of an observed value relative to a reference.

    Parameters
    ----------
    observed : float
        Value produced by the implementation under test.
    reference : float
        Known-good reference value.

    Returns
    -------
    float
        Percent bias: (observed - reference) / reference * 100.

    Raises
    ------
    ZeroDivisionError
        If reference is zero.
    """
    return (observed - reference) / reference * 100.0


def rmse(observed: list[float], reference: list[float]) -> float:
    """Compute root mean squared error between two equal-length sequences.

    Parameters
    ----------
    observed : list[float]
        Values produced by the implementation under test.
    reference : list[float]
        Known-good reference values.

    Returns
    -------
    float
        RMSE.

    Raises
    ------
    ValueError
        If the sequences have different lengths.
    """
    if len(observed) != len(reference):
        raise ValueError(
            f"observed and reference must have the same length "
            f"(got {len(observed)} vs {len(reference)})."
        )
    import math
    return math.sqrt(
        sum((o - r) ** 2 for o, r in zip(observed, reference, strict=True)) / len(observed)
    )


def within_pct(observed: float, reference: float, pct: float) -> bool:
    """Return True if observed is within pct% of reference.

    Parameters
    ----------
    observed : float
        Value produced by the implementation under test.
    reference : float
        Known-good reference value.
    pct : float
        Tolerance in percent (e.g. 5.0 means +/-5%).

    Returns
    -------
    bool
    """
    return abs(pct_bias(observed, reference)) <= pct


__all__ = ["pct_bias", "rmse", "within_pct"]
