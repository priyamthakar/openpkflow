"""Dissolution similarity metrics f1 and f2 (FDA 1997 guidance).

Both functions require the caller to supply arrays that are already aligned to
the same time points.  No interpolation or reindexing is performed.  Passing
arrays of different lengths, or arrays whose time points do not correspond,
will produce incorrect results or a ValueError.

References
----------
FDA Guidance for Industry: Dissolution Testing of Immediate Release Solid
Oral Dosage Forms (1997). CDER, U.S. Food and Drug Administration.
"""

from __future__ import annotations

import math
from collections.abc import Sequence


def _validate_profiles(
    reference: Sequence[float],
    test: Sequence[float],
    min_points: int = 3,
) -> tuple[list[float], list[float]]:
    """Validate and return cleaned float lists.

    Parameters
    ----------
    reference : Sequence[float]
        Reference (innovator) dissolution profile as percent released.
    test : Sequence[float]
        Test dissolution profile as percent released.
    min_points : int, optional
        Minimum required number of time points, by default 3.

    Returns
    -------
    tuple[list[float], list[float]]
        Materialized and validated (reference, test) lists of floats.

    Raises
    ------
    ValueError
        If arrays differ in length, are empty, contain fewer than *min_points*
        elements, contain NaN or infinite values, or contain values outside
        [0, 100].
    """
    ref = [float(x) for x in reference]
    tst = [float(x) for x in test]

    if len(ref) != len(tst):
        raise ValueError(
            f"reference and test must have the same length "
            f"(got {len(ref)} and {len(tst)})."
        )

    if len(ref) == 0:
        raise ValueError("reference and test must not be empty.")

    if len(ref) < min_points:
        raise ValueError(
            f"reference and test must have at least {min_points} timepoints "
            f"(got {len(ref)}).  FDA guidance recommends a minimum of 3."
        )

    for label, arr in (("reference", ref), ("test", tst)):
        for i, val in enumerate(arr):
            if not math.isfinite(val):
                raise ValueError(
                    f"{label}[{i}] = {val!r} is not finite (NaN or inf are not allowed)."
                )
            if val < 0.0 or val > 100.0:
                raise ValueError(
                    f"{label}[{i}] = {val} is outside [0, 100].  "
                    "Values must be percent released."
                )

    return ref, tst


def f2(reference: Sequence[float], test: Sequence[float]) -> float:
    """Compute the f2 similarity factor (FDA 1997 guidance).

    Parameters
    ----------
    reference : Sequence[float]
        Reference (innovator) dissolution profile as percent released,
        one value per matched time point.
    test : Sequence[float]
        Test dissolution profile as percent released,
        one value per matched time point.

    Returns
    -------
    float
        f2 value.  100 indicates identical profiles; values >= 50 indicate
        similarity per FDA 1997 guidance.

    Raises
    ------
    ValueError
        See `_validate_profiles` for all validation conditions.

    Notes
    -----
    Formula (FDA 1997)::

        f2 = 50 * log10(100 / sqrt(1 + (1/n) * sum((Rt - Tt)**2)))

    References
    ----------
    FDA Guidance for Industry: Dissolution Testing of Immediate Release
    Solid Oral Dosage Forms (1997). CDER, U.S. Food and Drug Administration.
    """
    ref, tst = _validate_profiles(reference, test)
    n = len(ref)
    mean_sq_diff = sum((r - t) ** 2 for r, t in zip(ref, tst)) / n
    return 50.0 * math.log10(100.0 / math.sqrt(1.0 + mean_sq_diff))


def f1(reference: Sequence[float], test: Sequence[float]) -> float:
    """Compute the f1 difference factor.

    Parameters
    ----------
    reference : Sequence[float]
        Reference (innovator) dissolution profile as percent released,
        one value per matched time point.
    test : Sequence[float]
        Test dissolution profile as percent released,
        one value per matched time point.

    Returns
    -------
    float
        f1 value.  0 indicates identical profiles; values <= 15 are
        generally considered acceptable.

    Raises
    ------
    ValueError
        See `_validate_profiles` for shared validation conditions.
        Also raised when the sum of reference values is zero.

    Notes
    -----
    Formula::

        f1 = (sum(|Rt - Tt|) / sum(Rt)) * 100

    References
    ----------
    FDA Guidance for Industry: Dissolution Testing of Immediate Release
    Solid Oral Dosage Forms (1997). CDER, U.S. Food and Drug Administration.
    """
    ref, tst = _validate_profiles(reference, test)
    ref_sum = sum(ref)
    if ref_sum == 0.0:
        raise ValueError(
            "Sum of reference values is zero; f1 is undefined when the reference "
            "profile is all zeros."
        )
    return (sum(abs(r - t) for r, t in zip(ref, tst)) / ref_sum) * 100.0
