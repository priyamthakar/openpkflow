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
import warnings
from collections.abc import Sequence
from dataclasses import dataclass
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
            f"reference and test must have the same length (got {len(ref)} and {len(tst)})."
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
                    f"{label}[{i}] = {val} is outside [0, 100].  Values must be percent released."
                )

    return ref, tst


def regulatory_cutoff(reference: Sequence[float], test: Sequence[float]) -> int:
    """Return how many leading timepoints the FDA 85% rule keeps for f2.

    Parameters
    ----------
    reference : Sequence[float]
        Reference mean profile as percent released.
    test : Sequence[float]
        Test mean profile as percent released.

    Returns
    -------
    int
        Number of leading timepoints up to and including the first one where
        both profiles exceed 85%, or all timepoints if none does.
    """
    for i, (r, t) in enumerate(zip(reference, test, strict=True)):
        if r > 85.0 and t > 85.0:
            return i + 1
    return len(reference)


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
        cutoff = regulatory_cutoff(ref, tst)
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

    Warns
    -----
    UserWarning
        Always. Without vessel-level data the covariance is estimated from the
        differences themselves, which makes MSD squared identically n - 1 for any
        non-identical pair of profiles. Use :func:`msd_vessels` instead.

    References
    ----------
    FDA Guidance for Industry: Polymer-Based Solid Oral Dosage Forms
    (1999). CDER. Section on Mahalanobis distance methodology.
    """
    warnings.warn(
        "msd() on mean profiles divides by the variance of the differences themselves, "
        "so MSD squared is always n_timepoints - 1 and is_similar carries no information. "
        "Use msd_vessels() with vessel-level data for a similarity decision.",
        UserWarning,
        stacklevel=2,
    )
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
        is_similar=msd_sq <= chi2_crit,
    )


def _chi2_ppf(p: float, df: int) -> float:
    """Chi-squared quantile function via Wilson-Hilferty approximation.

    Accurate to ~0.1% for df >= 3, which is sufficient for regulatory
    significance testing.
    """
    import scipy.stats as st

    return float(st.chi2.ppf(p, df))


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


@dataclass(frozen=True)
class MSDVesselResult:
    """Vessel-level Mahalanobis distance with the Tsong et al. (1996) similarity decision.

    Parameters
    ----------
    msd : float
        Mahalanobis distance between the test and reference mean profiles.
    ci_lower : float
        Lower bound of the Hotelling T-squared confidence region for the MSD.
    ci_upper : float
        Upper bound of the Hotelling T-squared confidence region for the MSD.
    similarity_limit : float
        MSD of a uniform ``similarity_limit_pct`` difference at every timepoint.
    similarity_limit_pct : float
        Allowed percentage-point difference at each timepoint.
    confidence_level : float
        Confidence level of the region (0.90 per Tsong et al.).
    f_critical : float
        F quantile with (p, n_R + n_T - p - 1) degrees of freedom.
    n_timepoints : int
        Number of timepoints p.
    n_reference : int
        Number of reference vessels.
    n_test : int
        Number of test vessels.
    is_similar : bool
        True when ci_upper <= similarity_limit.
    """

    msd: float
    ci_lower: float
    ci_upper: float
    similarity_limit: float
    similarity_limit_pct: float
    confidence_level: float
    f_critical: float
    n_timepoints: int
    n_reference: int
    n_test: int
    is_similar: bool

    @property
    def msd_squared(self) -> float:
        """Squared Mahalanobis distance."""
        return self.msd**2

    def summary(self) -> str:
        """Return a textual summary of the vessel-level MSD result.

        Returns
        -------
        str
            Multi-line summary with MSD, confidence region, limit, and verdict.
        """
        verdict = "SIMILAR" if self.is_similar else "NOT SIMILAR"
        level = self.confidence_level * 100.0
        return (
            f"Mahalanobis Statistical Distance (Tsong et al. 1996)\n"
            f"====================================================\n"
            f"Timepoints: {self.n_timepoints}  |  Vessels R/T: "
            f"{self.n_reference}/{self.n_test}\n"
            f"MSD: {self.msd:.4f}\n"
            f"{level:.0f}% CI: [{self.ci_lower:.4f}, {self.ci_upper:.4f}]\n"
            f"Similarity limit ({self.similarity_limit_pct:g}% per point): "
            f"{self.similarity_limit:.4f}\n"
            f"Verdict: {verdict}\n"
        )


def msd_vessels(
    reference: np.ndarray | Sequence[Sequence[float]],
    test: np.ndarray | Sequence[Sequence[float]],
    *,
    similarity_limit_pct: float = 10.0,
    confidence_level: float = 0.90,
) -> MSDVesselResult:
    """Model-independent multivariate MSD similarity test from vessel-level data.

    Parameters
    ----------
    reference : array-like, shape (n_R, p)
        Reference percent released, one row per vessel.
    test : array-like, shape (n_T, p)
        Test percent released, one row per vessel, same timepoints as reference.
    similarity_limit_pct : float, optional
        Allowed difference at every timepoint, by default 10 percentage points.
    confidence_level : float, optional
        Confidence level of the Hotelling region, by default 0.90.

    Returns
    -------
    MSDVesselResult
        MSD, its confidence region, the similarity limit, and the decision.

    Raises
    ------
    ValueError
        If shapes mismatch, values are non-finite or outside [0, 100], there are
        too few vessels for p timepoints (n_R + n_T - p - 1 < 1), or the pooled
        covariance matrix is singular (e.g. zero-variance plateau timepoints).

    References
    ----------
    Tsong Y, Hammerstrom T, Sathe P, Shah VP (1996). Statistical assessment of
    mean differences between two dissolution data sets. Drug Inf J 30:1105-1112.
    FDA Guidance for Industry: SUPAC-MR (1997), Appendix B.
    """
    ref = np.asarray(reference, dtype=float)
    tst = np.asarray(test, dtype=float)
    if ref.ndim != 2 or tst.ndim != 2:
        raise ValueError("reference and test must be 2-D arrays (n_vessels, n_timepoints).")
    if ref.shape[1] != tst.shape[1]:
        raise ValueError(
            f"reference and test must have the same number of timepoints "
            f"(got {ref.shape[1]} and {tst.shape[1]})."
        )
    for label, arr in (("reference", ref), ("test", tst)):
        if not np.all(np.isfinite(arr)):
            raise ValueError(f"{label} contains NaN or infinite values.")
        if np.any(arr < 0.0) or np.any(arr > 100.0):
            raise ValueError(f"{label} values must be percent released in [0, 100].")
    if not 0.0 < confidence_level < 1.0:
        raise ValueError(f"confidence_level must be in (0, 1) (got {confidence_level}).")
    if similarity_limit_pct <= 0.0:
        raise ValueError(f"similarity_limit_pct must be > 0 (got {similarity_limit_pct}).")

    n_r, p = ref.shape
    n_t = tst.shape[0]
    if p < 2:
        raise ValueError("MSD requires at least 2 timepoints.")
    df2 = n_r + n_t - p - 1
    if n_r < 2 or n_t < 2 or df2 < 1:
        raise ValueError(
            f"MSD needs n_R + n_T - p - 1 >= 1 and >= 2 vessels per product "
            f"(got n_R={n_r}, n_T={n_t}, p={p})."
        )

    pooled = ((n_r - 1) * np.cov(ref, rowvar=False) + (n_t - 1) * np.cov(tst, rowvar=False)) / (
        n_r + n_t - 2
    )
    if np.linalg.matrix_rank(pooled) < p:
        raise ValueError(
            "Pooled variance-covariance matrix is singular (for example, timepoints "
            "where every vessel reads the same value); MSD cannot be evaluated."
        )
    s_inv = np.linalg.inv(pooled)
    diff = tst.mean(axis=0) - ref.mean(axis=0)
    msd_val = math.sqrt(max(float(diff @ s_inv @ diff), 0.0))

    import scipy.stats as st

    # Hotelling region {y : k (y - d)' S^-1 (y - d) <= F} is a ball of radius
    # sqrt(F / k) in the S^-1 metric, so the MSD bounds are msd -/+ that radius.
    k = (n_r * n_t / (n_r + n_t)) * df2 / ((n_r + n_t - 2) * p)
    f_crit = float(st.f.ppf(confidence_level, p, df2))
    radius = math.sqrt(f_crit / k)
    limit_vec = np.full(p, float(similarity_limit_pct))
    limit = math.sqrt(float(limit_vec @ s_inv @ limit_vec))
    ci_upper = msd_val + radius

    return MSDVesselResult(
        msd=msd_val,
        ci_lower=max(msd_val - radius, 0.0),
        ci_upper=ci_upper,
        similarity_limit=limit,
        similarity_limit_pct=float(similarity_limit_pct),
        confidence_level=float(confidence_level),
        f_critical=f_crit,
        n_timepoints=p,
        n_reference=n_r,
        n_test=n_t,
        is_similar=ci_upper <= limit,
    )
