"""Two one-sided tests (TOST) for 2x2 crossover bioequivalence.

Reference
---------
Schuirmann, D.J. (1987). A comparison of the Two One-Sided Tests Procedure and
the Power Approach for assessing the equivalence of average bioavailability.
Journal of Pharmacokinetics and Biopharmaceutics, 15(6), 657-680.
DOI: 10.1007/BF01068419

Phillips, K.F. (1990). Power of the two one-sided tests procedure in
bioequivalence. J Pharmacokinet Biopharm, 18(2):137-144.
DOI: 10.1007/BF01063556

Diletti, E., Hauschke, D., Steinijans, V.W. (1991). Sample size determination
for bioequivalence assessment by means of confidence intervals.
Int J Clin Pharmacol Ther Toxicol, 29(1):1-8.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field

from scipy.stats import nct
from scipy.stats import t as t_dist


@dataclass
class BETOSTResult:
    """Raw output from :func:`be_tost`.

    Parameters
    ----------
    n : int
        Number of subjects.
    gmr : float
        Geometric mean ratio (test / reference).
    gmr_lower_90ci : float
        Lower bound of the 90% confidence interval for GMR.
    gmr_upper_90ci : float
        Upper bound of the 90% confidence interval for GMR.
    be_lower : float
        Lower acceptance limit (e.g. 0.80).
    be_upper : float
        Upper acceptance limit (e.g. 1.25).
    bioequivalent : bool
        True when gmr_lower_90ci >= be_lower and gmr_upper_90ci <= be_upper.
    cv_intra_pct : float
        Intra-subject coefficient of variation (%).
    alpha : float
        One-sided significance level used (0.05 gives a 90% CI).
    log_diffs : list[float]
        Within-subject log(test/reference) differences.
    """

    n: int
    gmr: float
    gmr_lower_90ci: float
    gmr_upper_90ci: float
    be_lower: float
    be_upper: float
    bioequivalent: bool
    cv_intra_pct: float
    alpha: float
    log_diffs: list[float] = field(repr=False)


def be_tost(
    reference: Sequence[float],
    test: Sequence[float],
    *,
    be_lower: float = 0.80,
    be_upper: float = 1.25,
    alpha: float = 0.05,
) -> BETOSTResult:
    """Two One-Sided Tests (TOST) for average bioequivalence.

    Computes the geometric mean ratio (GMR) and its 90% confidence interval from
    within-subject paired log-differences for a 2x2 crossover design.  The
    decision follows FDA 2003 guidance: bioequivalent when the 90% CI lies
    entirely within [be_lower, be_upper].

    Parameters
    ----------
    reference : sequence of float
        Per-subject PK parameter values for the reference formulation.
        Must be positive.
    test : sequence of float
        Per-subject PK parameter values for the test formulation.
        Must be positive and same length as *reference*.
    be_lower : float, optional
        Lower acceptance limit.  Default 0.80 (FDA/EMA standard).
    be_upper : float, optional
        Upper acceptance limit.  Default 1.25 (FDA/EMA standard).
    alpha : float, optional
        One-sided significance level.  Default 0.05 (yields a 90% CI).

    Returns
    -------
    BETOSTResult
        GMR, 90% CI bounds, bioequivalence decision, and intra-subject CV%.

    Raises
    ------
    ValueError
        If reference and test have different lengths, fewer than 2 subjects, or
        contain non-positive values.

    References
    ----------
    Schuirmann (1987) J Pharmacokinet Biopharm 15(6):657-680.
    FDA (2003) Guidance for Industry: Bioavailability and Bioequivalence Studies
        for Orally Administered Drug Products -- General Considerations.
    """
    ref = list(reference)
    tst = list(test)
    n = len(ref)

    if len(tst) != n:
        raise ValueError(f"reference and test must have the same length (got {n} vs {len(tst)}).")
    if n < 2:
        raise ValueError(f"at least 2 subjects are required (got {n}).")
    if any(v <= 0.0 for v in ref):
        raise ValueError("all reference values must be positive.")
    if any(v <= 0.0 for v in tst):
        raise ValueError("all test values must be positive.")
    if not (0.0 < be_lower < be_upper):
        raise ValueError(
            f"be_lower must be positive and less than be_upper (got {be_lower}, {be_upper})."
        )

    log_diffs = [math.log(t / r) for r, t in zip(ref, tst, strict=True)]
    d_bar = sum(log_diffs) / n

    s_d = 0.0 if n == 1 else math.sqrt(sum((d - d_bar) ** 2 for d in log_diffs) / (n - 1))

    se = s_d / math.sqrt(n)

    t_crit = float(t_dist.ppf(1.0 - alpha, df=n - 1))

    lower_log = d_bar - t_crit * se
    upper_log = d_bar + t_crit * se

    gmr = math.exp(d_bar)
    gmr_lower = math.exp(lower_log)
    gmr_upper = math.exp(upper_log)

    bioequivalent = gmr_lower >= be_lower and gmr_upper <= be_upper

    # Intra-subject CV% for a paired/crossover design:
    # Var(log T - log R) = 2 * sigma_w^2, so sigma_w^2 = s_d^2 / 2.
    # CV% = sqrt(exp(sigma_w^2) - 1) * 100  (Chow & Liu 2008; Hauschke et al.)
    sigma_w2 = (s_d**2) / 2.0
    cv_intra = math.sqrt(math.exp(sigma_w2) - 1.0) * 100.0

    return BETOSTResult(
        n=n,
        gmr=gmr,
        gmr_lower_90ci=gmr_lower,
        gmr_upper_90ci=gmr_upper,
        be_lower=be_lower,
        be_upper=be_upper,
        bioequivalent=bioequivalent,
        cv_intra_pct=cv_intra,
        alpha=alpha,
        log_diffs=log_diffs,
    )


def be_tost_power(
    gmr: float,
    cv: float,
    n: int,
    *,
    be_lower: float = 0.80,
    be_upper: float = 1.25,
    alpha: float = 0.05,
) -> float:
    """Statistical power of the 2x2 crossover TOST bioequivalence test.

    Computes the probability of declaring bioequivalence when the true
    geometric mean ratio is *gmr* and the intra-subject CV is *cv*,
    given *n* subjects in a standard 2x2 crossover trial.

    Uses the non-central t-distribution method (Phillips 1990; Diletti et
    al. 1991).  Matches PowerTOST `power.TOST(method="exact")`.

    Parameters
    ----------
    gmr : float
        True geometric mean ratio (test / reference).  Must be > 0.
    cv : float
        Intra-subject coefficient of variation as a fraction
        (e.g. 0.15 for 15%).  Must be > 0.
    n : int
        Number of subjects.  Must be >= 3 (df >= 1).
    be_lower : float, optional
        Lower acceptance limit.  Default 0.80.
    be_upper : float, optional
        Upper acceptance limit.  Default 1.25.
    alpha : float, optional
        One-sided significance level.  Default 0.05 (90% CI).

    Returns
    -------
    float
        Probability of passing TOST (0.0 to 1.0).

    Raises
    ------
    ValueError
        If *gmr* or *cv* is non-positive, or *n* < 3.

    References
    ----------
    Phillips KF (1990) J Pharmacokinet Biopharm 18(2):137-144.
    Diletti E, Hauschke D, Steinijans VW (1991)
        Int J Clin Pharmacol Ther Toxicol 29(1):1-8.
    """
    if gmr <= 0.0:
        raise ValueError(f"gmr must be positive (got {gmr}).")
    if cv <= 0.0:
        raise ValueError(f"cv must be positive (got {cv}).")
    if n < 3:
        raise ValueError(f"n must be at least 3 (got {n}).")

    sigma_w = math.sqrt(math.log(1.0 + cv**2))
    se = sigma_w * math.sqrt(2.0 / n)
    df = n - 2

    t_crit = float(t_dist.ppf(1.0 - alpha, df))
    delta_l = math.log(gmr / be_lower) / se
    delta_u = math.log(be_upper / gmr) / se

    power = 1.0 - nct.cdf(t_crit, df, delta_u) - nct.cdf(t_crit, df, delta_l)
    return float(max(0.0, min(1.0, power)))


def be_sample_size(
    gmr: float,
    cv: float,
    target_power: float = 0.80,
    *,
    be_lower: float = 0.80,
    be_upper: float = 1.25,
    alpha: float = 0.05,
    max_n: int = 1000,
) -> tuple[int, float]:
    """Sample size for a 2x2 crossover TOST bioequivalence study.

    Finds the smallest *n* such that :func:`be_tost_power` >= *target_power*.
    Uses sequential integer search starting from 2.

    Parameters
    ----------
    gmr : float
        Assumed true geometric mean ratio (test / reference).  Must be > 0.
    cv : float
        Assumed intra-subject CV as a fraction (e.g. 0.20 for 20%).  Must be > 0.
    target_power : float, optional
        Desired statistical power.  Default 0.80 (FDA/EMA standard).
    be_lower : float, optional
        Lower acceptance limit.  Default 0.80.
    be_upper : float, optional
        Upper acceptance limit.  Default 1.25.
    alpha : float, optional
        One-sided significance level.  Default 0.05.
    max_n : int, optional
        Maximum subjects to consider.  Default 1000.

    Returns
    -------
    tuple[int, float]
        Required sample size and the achieved power at that size.

    Raises
    ------
    ValueError
        If *gmr*, *cv*, or *target_power* is out of range.
    RuntimeError
        If *max_n* is reached without achieving *target_power*.

    References
    ----------
    Diletti E, Hauschke D, Steinijans VW (1991)
        Int J Clin Pharmacol Ther Toxicol 29(1):1-8.
    FDA (2001) Guidance: Statistical Approaches to Establishing Bioequivalence.
    """
    if not (0.0 < target_power < 1.0):
        raise ValueError(f"target_power must be in (0, 1) (got {target_power}).")

    achieved = 0.0
    for n in range(4, max_n + 1, 2):
        achieved = be_tost_power(
            gmr,
            cv,
            n,
            be_lower=be_lower,
            be_upper=be_upper,
            alpha=alpha,
        )
        if achieved >= target_power:
            return n, achieved

    raise RuntimeError(
        f"Target power {target_power} not reached within max_n={max_n}. "
        f"Last power at n={max_n}: {achieved:.6f}."
    )
