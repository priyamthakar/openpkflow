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
from typing import Literal


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


def f2(
    reference: Sequence[float],
    test: Sequence[float],
    *,
    method: Literal["all_points", "regulatory"] = "all_points",
) -> float:
    """Compute the f2 similarity factor (FDA 1997 guidance).

    Parameters
    ----------
    reference : Sequence[float]
        Reference (innovator) dissolution profile as percent released,
        one value per matched time point.
    test : Sequence[float]
        Test dissolution profile as percent released,
        one value per matched time point.
    method : {"all_points", "regulatory"}, optional
        Timepoint selection method, by default "all_points".

        - ``"all_points"`` — uses every supplied timepoint (original behaviour,
          backwards-compatible default).
        - ``"regulatory"`` — applies the FDA 85% rule: at most one timepoint
          where both the reference and test means exceed 85% may be included.
          Trimming starts from the end: the first index where both ref[i] > 85
          and tst[i] > 85 is found, and all timepoints after that index are
          discarded. A ``ValueError`` is raised if fewer than 3 points remain
          after trimming.

    Returns
    -------
    float
        f2 value.  100 indicates identical profiles; values >= 50 indicate
        similarity per FDA 1997 guidance.

    Raises
    ------
    ValueError
        See `_validate_profiles` for all validation conditions.
        Also raised when ``method="regulatory"`` leaves fewer than 3 timepoints,
        or when an unknown method string is supplied.

    Notes
    -----
    Formula (FDA 1997)::

        f2 = 50 * log10(100 / sqrt(1 + (1/n) * sum((Rt - Tt)**2)))

    The 85% rule (regulatory method) is described in FDA guidance: only one
    timepoint above 85% dissolution for both profiles is permitted when
    computing f2, to avoid artificially inflating the similarity factor in the
    plateau region of the dissolution curve.

    References
    ----------
    FDA Guidance for Industry: Dissolution Testing of Immediate Release
    Solid Oral Dosage Forms (1997). CDER, U.S. Food and Drug Administration.
    """
    ref, tst = _validate_profiles(reference, test)

    if method == "regulatory":
        # FDA guidance: only one timepoint above 85% for both profiles
        cutoff = len(ref)
        for i, (r, t) in enumerate(zip(ref, tst)):
            if r > 85.0 and t > 85.0:
                cutoff = i + 1  # include this point, exclude all after
                break
        ref = ref[:cutoff]
        tst = tst[:cutoff]
        if len(ref) < 3:
            raise ValueError(
                f"After applying the regulatory 85% rule, fewer than 3 timepoints "
                f"remain ({len(ref)}). f2 cannot be computed."
            )
    elif method != "all_points":
        raise ValueError(f"Unknown method {method!r}. Use 'all_points' or 'regulatory'.")

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
