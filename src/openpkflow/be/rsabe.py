"""FDA partial-replicate reference-scaled average bioequivalence (RSABE)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from scipy.stats import chi2
from scipy.stats import t as t_dist

RsabeDecision = Literal["PASS", "FAIL", "NOT_EVALUABLE"]

_EXPECTED_TREATMENT = {
    "TRR": {1: "T", 2: "R", 3: "R"},
    "RTR": {1: "R", 2: "T", 3: "R"},
    "RRT": {1: "R", 2: "R", 3: "T"},
}
_REGULATORY_CONSTANT = 0.25


@dataclass(frozen=True)
class FdaRsabeResult:
    """FDA partial-replicate RSABE result for a single endpoint."""

    parameter: str
    decision: RsabeDecision
    design: str
    jurisdiction: Literal["FDA"]
    validation_status: Literal["VALIDATED"]
    message: str
    n_subjects: int
    alpha: float
    confidence_level_pct: float
    delta_hat: float
    delta_ci_lower: float
    delta_ci_upper: float
    gmr: float
    gmr_ci_lower: float
    gmr_ci_upper: float
    sigma_wr: float
    sigma_wr_ci_lower: float
    sigma_wr_ci_upper: float
    cv_wr_pct: float
    highly_variable: bool
    theta: float
    aggregate_criterion_point: float
    aggregate_criterion_upper: float
    point_estimate_constraint_met: bool

    @property
    def bioequivalent(self) -> bool:
        """Return whether the decision is PASS."""
        return self.decision == "PASS"

    def summary(self) -> str:
        """Return an ASCII summary of the RSABE result."""
        return "\n".join(
            [
                "FDA Partial-Replicate RSABE",
                "=" * 40,
                f"Parameter        : {self.parameter}",
                f"Subjects (n)     : {self.n_subjects}",
                f"GMR (T/R)        : {self.gmr:.4f}",
                f"GMR 90% CI       : [{self.gmr_ci_lower:.4f}, {self.gmr_ci_upper:.4f}]",
                f"CVwR             : {self.cv_wr_pct:.1f}% "
                f"({'highly variable' if self.highly_variable else 'not highly variable'})",
                f"Aggregate crit.  : point={self.aggregate_criterion_point:.4f}, "
                f"95% upper={self.aggregate_criterion_upper:.4f}",
                f"Point est. limit : {'met' if self.point_estimate_constraint_met else 'not met'}",
                f"Decision         : {self.decision}",
            ]
        )

    def report(self, path: str | Path, format: str | None = None) -> None:
        """Write an RSABE report as HTML or Markdown."""
        from openpkflow.be.rsabe_reporting import report_rsabe

        report_rsabe(self, path, format=format)


def fda_partial_replicate_rsabe(
    data: pd.DataFrame,
    *,
    parameter: str,
    subject_col: str = "subject",
    sequence_col: str = "sequence",
    period_col: str = "period",
    treatment_col: str = "treatment",
    value_col: str | None = None,
    alpha: float = 0.05,
    sigma_wr_floor: float = _REGULATORY_CONSTANT,
    highly_variable_cv_pct: float = 30.0,
) -> FdaRsabeResult:
    """Evaluate FDA partial-replicate (TRR/RTR/RRT) reference-scaled ABE.

    Implements the method-of-moments estimators and the FDA working-group
    linearized aggregate criterion (Haidar et al. 2007, 2008) using the
    Hyslop-Hsuan-Holder (2000) confidence-bound combination.

    Parameters
    ----------
    data : pd.DataFrame
        Long-format partial-replicate data: one row per subject and period.
    parameter : str
        Endpoint label used in result output.
    subject_col, sequence_col, period_col, treatment_col : str, optional
        Required design column names.
    value_col : str or None, optional
        Endpoint column. Defaults to ``parameter``.
    alpha : float, optional
        One-sided significance level; the derived confidence level is
        ``(1 - 2 * alpha) * 100`` percent (0.05 gives the standard 90% CI).
    sigma_wr_floor : float, optional
        Regulatory floor applied to sigma_wR inside the aggregate criterion
        (FDA sets this to 0.25 when the observed sigma_wR is smaller).
    highly_variable_cv_pct : float, optional
        Minimum reference intra-subject %CV for RSABE to apply. Below this,
        RSABE is NOT_EVALUABLE and standard average BE should be used instead.

    Returns
    -------
    FdaRsabeResult
        Method-of-moments diagnostics and the PASS/FAIL/NOT_EVALUABLE decision.

    Raises
    ------
    ValueError
        If the data are not a complete TRR/RTR/RRT partial-replicate design.

    References
    ----------
    Patterson SD, Jones B (2012) Viewpoint: observations on scaled average
    bioequivalence. Pharmaceutical Statistics 11(1):1-7. DOI: 10.1002/pst.498.
    Hyslop T, Hsuan F, Holder DJ (2000) A small sample confidence interval
    approach to assess individual bioequivalence. Statistics in Medicine
    19:2885-2897.
    """
    endpoint = value_col or parameter
    frame = _validate_partial_replicate(
        data, endpoint, subject_col, sequence_col, period_col, treatment_col
    )
    n = frame["subject"].nunique()
    df = n - 3

    wide = frame.pivot(index="subject", columns="period", values="log_value")
    sequence_by_subject = frame.drop_duplicates("subject").set_index("subject")["sequence"]
    sequence = sequence_by_subject.loc[wide.index]

    p1, p2, p3 = wide[1].to_numpy(), wide[2].to_numpy(), wide[3].to_numpy()
    is_trr = (sequence == "TRR").to_numpy()
    is_rtr = (sequence == "RTR").to_numpy()

    contrast = np.where(
        is_trr,
        p1 - (p2 + p3) / 2.0,
        np.where(is_rtr, p2 - (p1 + p3) / 2.0, p3 - (p1 + p2) / 2.0),
    )
    r1 = np.where(is_trr, p2, np.where(is_rtr, p1, p1))
    r2 = np.where(is_trr, p3, np.where(is_rtr, p3, p2))

    delta_hat = float(np.mean(contrast))
    se_delta = float(np.sqrt(np.var(contrast, ddof=1) / n))
    t_crit = float(t_dist.ppf(1.0 - alpha, df))
    delta_ci = (delta_hat - t_crit * se_delta, delta_hat + t_crit * se_delta)

    sigma2_wr = float(np.sum((r1 - r2) ** 2) / (2.0 * n))
    chi_lo = float(chi2.ppf(alpha, df))
    chi_hi = float(chi2.ppf(1.0 - alpha, df))
    sigma2_wr_ci = (sigma2_wr * df / chi_hi, sigma2_wr * df / chi_lo)
    sigma_wr = math.sqrt(sigma2_wr)
    sigma_wr_ci = (math.sqrt(sigma2_wr_ci[0]), math.sqrt(sigma2_wr_ci[1]))
    cv_wr_pct = math.sqrt(math.exp(sigma2_wr) - 1.0) * 100.0
    highly_variable = cv_wr_pct >= highly_variable_cv_pct

    theta = (math.log(1.25) / _REGULATORY_CONSTANT) ** 2
    d2_point = delta_hat**2
    d2_upper = max(delta_ci[0] ** 2, delta_ci[1] ** 2)
    sigma_wr_point_used = max(sigma_wr, sigma_wr_floor)
    sigma_wr_upper_used = max(sigma_wr_ci[1], sigma_wr_floor)
    ts_point = theta * sigma_wr_point_used**2
    ts_upper = theta * sigma_wr_upper_used**2
    agg_point = d2_point - ts_point
    agg_upper = agg_point + math.sqrt((d2_upper - d2_point) ** 2 + (ts_upper - ts_point) ** 2)

    gmr = math.exp(delta_hat)
    gmr_ci = (math.exp(delta_ci[0]), math.exp(delta_ci[1]))
    point_estimate_ok = 0.80 < gmr < 1.25

    decision: RsabeDecision
    if not highly_variable:
        decision = "NOT_EVALUABLE"
        message = (
            f"Reference intra-subject CV ({cv_wr_pct:.1f}%) is below the "
            f"{highly_variable_cv_pct:g}% RSABE threshold; use standard average "
            "bioequivalence (formal_be_anova) instead."
        )
    elif not point_estimate_ok:
        decision = "FAIL"
        message = f"Point estimate constraint not met: GMR = {gmr:.4f} is outside (0.80, 1.25)."
    elif agg_upper < 0.0:
        decision = "PASS"
        message = "SABE demonstrated: aggregate criterion 95% upper bound < 0."
    else:
        decision = "FAIL"
        message = "SABE not demonstrated: aggregate criterion 95% upper bound >= 0."

    return FdaRsabeResult(
        parameter=parameter,
        decision=decision,
        design="partial_replicate_2x2x3",
        jurisdiction="FDA",
        validation_status="VALIDATED",
        message=message,
        n_subjects=n,
        alpha=alpha,
        confidence_level_pct=(1.0 - 2.0 * alpha) * 100.0,
        delta_hat=delta_hat,
        delta_ci_lower=delta_ci[0],
        delta_ci_upper=delta_ci[1],
        gmr=gmr,
        gmr_ci_lower=gmr_ci[0],
        gmr_ci_upper=gmr_ci[1],
        sigma_wr=sigma_wr,
        sigma_wr_ci_lower=sigma_wr_ci[0],
        sigma_wr_ci_upper=sigma_wr_ci[1],
        cv_wr_pct=cv_wr_pct,
        highly_variable=highly_variable,
        theta=theta,
        aggregate_criterion_point=agg_point,
        aggregate_criterion_upper=agg_upper,
        point_estimate_constraint_met=point_estimate_ok,
    )


def _validate_partial_replicate(
    data: pd.DataFrame,
    value_col: str,
    subject_col: str,
    sequence_col: str,
    period_col: str,
    treatment_col: str,
) -> pd.DataFrame:
    required = [subject_col, sequence_col, period_col, treatment_col, value_col]
    missing = [column for column in required if column not in data.columns]
    if missing:
        raise ValueError(f"Missing required RSABE columns: {missing!r}.")
    frame = data[required].copy()
    frame.columns = ["subject", "sequence", "period", "treatment", "value"]
    if frame.isna().any().any():
        raise ValueError("RSABE data must not contain missing values.")
    frame["sequence"] = frame["sequence"].astype(str).str.upper()
    frame["treatment"] = frame["treatment"].astype(str).str.upper()
    frame["period"] = pd.to_numeric(frame["period"], errors="coerce")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    if not np.isfinite(frame["period"]).all() or not np.isfinite(frame["value"]).all():
        raise ValueError("RSABE periods and endpoint values must be finite.")
    if (frame["value"] <= 0.0).any():
        raise ValueError("RSABE endpoint values must be > 0 for log analysis.")
    if set(frame["sequence"]) != {"TRR", "RTR", "RRT"}:
        raise ValueError("FDA partial-replicate RSABE requires TRR, RTR, and RRT sequences.")
    if set(frame["period"]) != {1, 2, 3}:
        raise ValueError("FDA partial-replicate RSABE requires periods 1, 2, and 3.")
    if frame.duplicated(["subject", "period"]).any():
        raise ValueError("RSABE data must contain one observation per subject and period.")
    subject_counts = frame.groupby("subject", sort=False).size()
    if not (subject_counts == 3).all():
        raise ValueError("FDA partial-replicate RSABE requires complete three-period subjects.")
    sequence_per_subject = frame.groupby("subject", sort=False)["sequence"].nunique()
    if not (sequence_per_subject == 1).all():
        raise ValueError("Each subject must have exactly one sequence assignment.")
    for row in frame.itertuples(index=False):
        if _EXPECTED_TREATMENT[row.sequence].get(int(row.period)) != row.treatment:
            raise ValueError("Treatment assignments must agree with sequence and period.")
    if frame["subject"].nunique() - 3 < 1:
        raise ValueError("FDA partial-replicate RSABE requires at least four subjects.")
    frame["log_value"] = np.log(frame["value"])
    return frame
