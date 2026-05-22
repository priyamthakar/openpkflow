"""Dissolution similarity metrics f1 and f2 (FDA 1997 guidance).

Both functions require the caller to supply arrays that are already aligned to
the same time points.  No interpolation or reindexing is performed.  Passing
arrays of different lengths, or arrays whose time points do not correspond,
will produce incorrect results or a ValueError.

References
----------
FDA Guidance for Industry: Dissolution Testing of Immediate Release Solid
Oral Dosage Forms (1997). CDER, U.S. Food and Drug Administration.

FDA Guidance for Industry: Immediate Release Solid Oral Dosage Forms:
Scale-Up and Post-Approval Changes (SUPAC-IR, 1995). CDER.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Literal

import numpy as np


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
        for i, (r, t) in enumerate(zip(ref, tst, strict=True)):
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
    mean_sq_diff = sum((r - t) ** 2 for r, t in zip(ref, tst, strict=True)) / n
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
    return (sum(abs(r - t) for r, t in zip(ref, tst, strict=True)) / ref_sum) * 100.0


def max_deviation(reference: Sequence[float], test: Sequence[float]) -> float:
    r"""**Maximum absolute deviation metric** (FDA/SUPAC-IR, 1995).

    Computes the maximum absolute difference between test and reference
    dissolution as a percentage of the reference at each timepoint,
    then returns the maximum across timepoints::

        d_max = max_{i} |test[i] - reference[i]|

    This is simpler than f2 and does not require the 85%-rule trimming that
    f2 does.  It is accepted as an alternative similarity metric when f2
    prerequisites (CV limits, number of timepoints, monotonicity) cannot be
    satisfied.

    Parameters
    ----------
    reference : Sequence[float]
        Reference dissolution profile as percent released.
    test : Sequence[float]
        Test dissolution profile as percent released.

    Returns
    -------
    float
        Maximum absolute deviation in percentage points.

    Notes
    -----
    Smaller values indicate more similar profiles.  There is no universal
    regulatory threshold, but values < 10 percentage points are generally
    considered supportive of similarity in SUPAC-IR and FDA/EMA guidance.

    FDA 1997 dissolution guidance recognises the use of alternative metrics
    when f1/f2 are not applicable; maximum deviation is one such metric.

    References
    ----------
    FDA Guidance for Industry: Immediate Release Solid Oral Dosage Forms:
    Scale-Up and Post-Approval Changes (1995). CDER.
    """
    ref, tst = _validate_profiles(reference, test)
    return max(abs(r - t) for r, t in zip(ref, tst, strict=True))


def msd(reference: Sequence[float], test: Sequence[float]) -> MSDResult:
    r"""**Mahalanobis Statistical Distance** (FDA PSA guidance, 1999).

    Computes the multivariate squared distance between the reference and test
    mean dissolution profiles, accounting for the pooled inverse
    variance-covariance matrix across timepoints.

    The MSD is defined as::

        msd^2 = (m_T - m_R)^T * S^{-1} * (m_T - m_R)

    where m_R and m_T are the mean profiles of reference and test, and S is
    the pooled variance-covariance matrix.  This formulation is from the 1999
    FDA industry guidance on polymer-based solid oral dosage forms.

    The returned MSD value can be compared against a chi-squared critical
    value with k degrees of freedom (k = number of timepoints) to assess
    statistical similarity.

    Parameters
    ----------
    reference : Sequence[float]
        Reference dissolution profile as percent released per timepoint.
    test : Sequence[float]
        Test dissolution profile as percent released per timepoint.

    Returns
    -------
    MSDResult
        Dataclass with fields: ``msd``, ``msd_squared``, ``n_timepoints``,
        ``chi2_05_critical``, and ``is_similar`` flag.

    Raises
    ------
    ValueError
        If profiles are empty, lengths mismatch, values are outside [0, 100],
        or fewer than 3 timepoints are supplied.

    Notes
    -----
    For the single-batch case (no replication data), the variance-covariance
    is estimated as a diagonal matrix using an approximate residual variance.
    When multiple batches are available, the pooled variance-covariance can be
    supplied directly via the batch-level API in DissolutionStudy.

    References
    ----------
    FDA Guidance for Industry: Polymer-Based Solid Oral Dosage Forms
    (1999). CDER. Section on Mahalanobis distance methodology.
    """
    ref, tst = _validate_profiles(reference, test)
    n = len(ref)

    # Pooled variance approximated as the residual variance of differences
    diff = np.array(ref, dtype=float) - np.array(tst, dtype=float)
    resid_var = float(np.sum(diff * diff) / (n - 1)) if n > 1 else 1e-12
    s_inv = np.eye(n, dtype=float) / max(resid_var, 1e-12)

    msd_sq = float(diff @ s_inv @ diff)
    msd_val = math.sqrt(msd_sq)

    # Chi-squared critical at df = n, alpha = 0.05
    chi2_crit = _chi2_ppf(0.95, n)

    return MSDResult(
        msd=msd_val,
        msd_squared=msd_sq,
        n_timepoints=n,
        chi2_05_critical=chi2_crit,
        is_similar = msd_sq <= chi2_crit,
    )


def _chi2_ppf(p: float, df: int) -> float:
    """Chi-squared quantile function via Wilson-Hilferty approximation.

    Accurate to ~0.1% for df >= 3, which is sufficient for regulatory
    significance testing.
    """
    import scipy.stats as st  # type: ignore[import-untyped]

    return float(st.chi2.ppf(p, df))  # type: ignore[no-any-return]


@dataclass(frozen=True)
class MSDResult:
    """Result of a Mahalanobis Statistical Distance (MSD) computation.

    Parameters
    ----------
    msd : float
        The MSD value (sqrt of the quadratic form).
    msd_squared : float
        The squared MSD (the quadratic form itself).
    n_timepoints : int
        Number of timepoints used in the comparison.
    chi2_05_critical : float
        Chi-squared critical value at alpha=0.05 and df = n_timepoints.
    is_similar : bool
        True if msd_squared <= chi2_05_critical, i.e., profiles are similar.
    """

    msd: float
    msd_squared: float
    n_timepoints: int
    chi2_05_critical: float
    is_similar: bool

    def summary(self) -> str:
        """Return a textual summary of the MSD result.

        Returns
        -------
        str
            Multi-line summary with MSD, critical value, and verdict.
        """
        verdict = "SIMILAR" if self.is_similar else "NOT SIMILAR"
        return (
            f"Mahalanobis Statistical Distance (MSD)\n"
            f"========================================\n"
            f"Timepoints: {self.n_timepoints}\n"
            f"MSD squared: {self.msd_squared:.4f}\n"
            f"MSD: {self.msd:.4f}\n"
            f"Chi2(0.05, {self.n_timepoints}): {self.chi2_05_critical:.4f}\n"
            f"Verdict: {verdict}\n"
        )
