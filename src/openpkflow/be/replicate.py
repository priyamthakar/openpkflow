"""Replicate-design bioequivalence screening utilities.

The functions in this module work on long-format replicate crossover data and
provide transparent average-BE and reference-scaled summary statistics. They are
intended for reproducible screening and validation workflows, not as a complete
replacement for jurisdiction-specific mixed-model/SAS submissions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from scipy.stats import t as t_dist


@dataclass
class ReplicateBEResult:
    """Summary of a replicate-design bioequivalence analysis.

    Parameters
    ----------
    n_subjects : int
        Number of subjects contributing at least one test and one reference
        observation.
    design : str
        Design label inferred from the sequence strings, such as ``"TRTR/RTRT"``
        or ``"TRR/RTR/RRT"``.
    gmr : float
        Geometric mean ratio, test/reference.
    gmr_lower_90ci, gmr_upper_90ci : float
        Conventional average-BE 90% confidence interval from within-subject
        test-minus-reference mean log differences.
    abe_pass : bool
        True when the conventional 90% CI lies inside ``be_lower`` and
        ``be_upper``.
    cv_wr_pct : float
        Reference within-subject CV%, estimated from repeated reference
        observations within subjects.
    swr : float
        Reference within-subject standard deviation on the log scale.
    scaled_lower, scaled_upper : float
        EMA-style scaled limits. The default uses 80-125% when CVwR <= 30%,
        otherwise ``exp(+/- 0.760 * swr)`` capped at the CVwR=50% limits.
    scaled_abe_pass : bool
        True when the conventional 90% CI lies inside scaled limits and the
        point estimate remains inside 80-125%.
    rsabe_point_criterion : float
        FDA-style point estimate of ``(mean log T/R)^2 - theta * swr^2`` with
        ``theta=(log(1.25)/0.25)^2``. Values <= 0 satisfy the scaled point
        criterion; this is not the required 95% upper confidence bound.
    rsabe_point_pass : bool
        True when ``rsabe_point_criterion <= 0`` and the point estimate remains
        inside 80-125%.
    analysis_note : str
        Explicit caveat about regulatory interpretation.
    subjects_df : pd.DataFrame
        Per-subject mean log T/R differences used for GMR and CI estimation.
    """

    parameter: str
    n_subjects: int
    design: str
    gmr: float
    gmr_lower_90ci: float
    gmr_upper_90ci: float
    be_lower: float
    be_upper: float
    abe_pass: bool
    cv_wr_pct: float
    swr: float
    scaled_lower: float
    scaled_upper: float
    scaled_abe_pass: bool
    rsabe_point_criterion: float
    rsabe_point_pass: bool
    analysis_note: str
    subjects_df: pd.DataFrame

    def summary(self) -> str:
        """Return a compact ASCII summary."""
        lines = [
            "Replicate BE Summary",
            "=" * 40,
            f"Parameter          : {self.parameter}",
            f"Design             : {self.design}",
            f"Subjects (n)       : {self.n_subjects}",
            f"GMR (T/R)          : {self.gmr:.4f}",
            f"90% CI             : [{self.gmr_lower_90ci:.4f}, {self.gmr_upper_90ci:.4f}]",
            f"ABE limits         : [{self.be_lower:.4f}, {self.be_upper:.4f}]",
            f"ABE conclusion     : {'PASS' if self.abe_pass else 'FAIL'}",
            f"CVwR               : {self.cv_wr_pct:.1f}%",
            f"Scaled limits      : [{self.scaled_lower:.4f}, {self.scaled_upper:.4f}]",
            f"Scaled ABE screen  : {'PASS' if self.scaled_abe_pass else 'FAIL'}",
            f"RSABE point screen : {'PASS' if self.rsabe_point_pass else 'FAIL'}",
            f"RSABE criterion    : {self.rsabe_point_criterion:.6f}",
            f"Note               : {self.analysis_note}",
        ]
        return "\n".join(lines)

    def to_dict(self) -> dict[str, object]:
        """Return scalar result fields as a plain dictionary."""
        return {
            "n_subjects": self.n_subjects,
            "parameter": self.parameter,
            "design": self.design,
            "gmr": self.gmr,
            "gmr_lower_90ci": self.gmr_lower_90ci,
            "gmr_upper_90ci": self.gmr_upper_90ci,
            "be_lower": self.be_lower,
            "be_upper": self.be_upper,
            "abe_pass": self.abe_pass,
            "cv_wr_pct": self.cv_wr_pct,
            "swr": self.swr,
            "scaled_lower": self.scaled_lower,
            "scaled_upper": self.scaled_upper,
            "scaled_abe_pass": self.scaled_abe_pass,
            "rsabe_point_criterion": self.rsabe_point_criterion,
            "rsabe_point_pass": self.rsabe_point_pass,
            "analysis_note": self.analysis_note,
        }

    def report(self, path: str | Path, format: str | None = None) -> None:
        """Write a replicate BE report to *path*."""
        from openpkflow.be.reporting import report_replicate_be

        report_replicate_be(self, path, format=format)


def cv_to_s_within(cv: float) -> float:
    """Convert within-subject CV fraction to log-scale standard deviation."""
    if cv < 0.0:
        raise ValueError(f"cv must be non-negative (got {cv}).")
    return math.sqrt(math.log(1.0 + cv**2))


def s_within_to_cv_pct(s_within: float) -> float:
    """Convert log-scale within-subject SD to CV%."""
    if s_within < 0.0:
        raise ValueError(f"s_within must be non-negative (got {s_within}).")
    return math.sqrt(math.exp(s_within**2) - 1.0) * 100.0


def ema_scaled_limits(
    swr: float,
    *,
    be_lower: float = 0.80,
    be_upper: float = 1.25,
    regulatory_constant: float = 0.760,
    cv_switch: float = 0.30,
    cv_cap: float = 0.50,
) -> tuple[float, float]:
    """Return EMA-style scaled BE limits from reference within-subject SD.

    The default applies standard 80-125% limits at CVwR <= 30%, scales as
    ``exp(+/- 0.760 * swr)`` above 30%, and caps widening at CVwR=50%.
    """
    if swr < 0.0:
        raise ValueError(f"swr must be non-negative (got {swr}).")
    if not (0.0 < be_lower < be_upper):
        raise ValueError("be_lower must be positive and less than be_upper.")

    cv_wr = math.sqrt(math.exp(swr**2) - 1.0)
    if cv_wr <= cv_switch:
        return be_lower, be_upper

    capped_swr = min(swr, cv_to_s_within(cv_cap))
    upper = math.exp(regulatory_constant * capped_swr)
    lower = 1.0 / upper
    return lower, upper


def replicate_be(
    data: pd.DataFrame,
    *,
    value_col: str,
    subject_col: str = "subject",
    sequence_col: str = "sequence",
    period_col: str = "period",
    treatment_col: str = "treatment",
    test_label: str = "T",
    reference_label: str = "R",
    be_lower: float = 0.80,
    be_upper: float = 1.25,
    alpha: float = 0.05,
) -> ReplicateBEResult:
    """Analyze long-format full or partial replicate BE data.

    Required columns are subject, sequence, period, treatment, and a positive
    PK parameter value. Supported sequence labels are not hard-coded; any design
    with at least one test and at least two reference observations overall can be
    summarized. Common examples include TRTR/RTRT and TRR/RTR/RRT.
    """
    required = [subject_col, sequence_col, period_col, treatment_col, value_col]
    missing = [c for c in required if c not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing!r}")
    if not (0.0 < be_lower < be_upper):
        raise ValueError("be_lower must be positive and less than be_upper.")
    if not (0.0 < alpha < 0.5):
        raise ValueError(f"alpha must be in (0, 0.5), got {alpha}.")

    df = data[required].copy()
    df[treatment_col] = df[treatment_col].astype(str).str.upper()
    test_label = test_label.upper()
    reference_label = reference_label.upper()

    unknown = sorted(set(df[treatment_col]) - {test_label, reference_label})
    if unknown:
        raise ValueError(
            f"Unknown treatment labels {unknown!r}; expected {test_label!r}/{reference_label!r}."
        )

    values = df[value_col].astype(float)
    if (values <= 0.0).any():
        raise ValueError(f"all {value_col!r} values must be positive.")
    df["_log_value"] = values.map(math.log)

    subject_rows: list[dict[str, object]] = []
    r_ss = 0.0
    r_df = 0

    for subject, sub in df.groupby(subject_col, sort=True):
        t_vals = sub.loc[sub[treatment_col] == test_label, "_log_value"].tolist()
        r_vals = sub.loc[sub[treatment_col] == reference_label, "_log_value"].tolist()
        if not t_vals or not r_vals:
            continue

        t_mean = sum(t_vals) / len(t_vals)
        r_mean = sum(r_vals) / len(r_vals)
        diff = t_mean - r_mean
        subject_rows.append(
            {
                "subject": subject,
                "n_test": len(t_vals),
                "n_reference": len(r_vals),
                "mean_log_test": t_mean,
                "mean_log_reference": r_mean,
                "log_diff": diff,
                "ratio": math.exp(diff),
            }
        )

        if len(r_vals) >= 2:
            r_bar = sum(r_vals) / len(r_vals)
            r_ss += sum((v - r_bar) ** 2 for v in r_vals)
            r_df += len(r_vals) - 1

    subjects_df = pd.DataFrame(subject_rows)
    n = len(subjects_df)
    if n < 2:
        raise ValueError(
            "at least 2 subjects with both test and reference observations are required."
        )
    if r_df <= 0:
        raise ValueError("replicate BE requires repeated reference observations to estimate CVwR.")

    diffs = subjects_df["log_diff"].astype(float).tolist()
    mean_diff = sum(diffs) / n
    sd_diff = math.sqrt(sum((d - mean_diff) ** 2 for d in diffs) / (n - 1))
    se = sd_diff / math.sqrt(n)
    t_crit = float(t_dist.ppf(1.0 - alpha, df=n - 1))

    gmr = math.exp(mean_diff)
    lower_ci = math.exp(mean_diff - t_crit * se)
    upper_ci = math.exp(mean_diff + t_crit * se)
    abe_pass = lower_ci >= be_lower and upper_ci <= be_upper

    swr = math.sqrt(r_ss / r_df)
    cv_wr_pct = s_within_to_cv_pct(swr)
    scaled_lower, scaled_upper = ema_scaled_limits(swr, be_lower=be_lower, be_upper=be_upper)
    point_in_standard_limits = be_lower <= gmr <= be_upper
    scaled_abe_pass = (
        lower_ci >= scaled_lower and upper_ci <= scaled_upper and point_in_standard_limits
    )

    theta = (math.log(1.25) / 0.25) ** 2
    rsabe_point_criterion = mean_diff**2 - theta * swr**2
    rsabe_point_pass = rsabe_point_criterion <= 0.0 and point_in_standard_limits

    sequence_labels = sorted(str(s) for s in df[sequence_col].dropna().unique())
    design = "/".join(sequence_labels) if sequence_labels else "replicate"

    note = (
        "Research-grade replicate BE screen: conventional CI and scaled summary "
        "statistics are reported, but jurisdiction-specific mixed-model degrees "
        "of freedom and FDA RSABE 95% upper-bound calculations are not implemented."
    )

    return ReplicateBEResult(
        parameter=value_col,
        n_subjects=n,
        design=design,
        gmr=gmr,
        gmr_lower_90ci=lower_ci,
        gmr_upper_90ci=upper_ci,
        be_lower=be_lower,
        be_upper=be_upper,
        abe_pass=abe_pass,
        cv_wr_pct=cv_wr_pct,
        swr=swr,
        scaled_lower=scaled_lower,
        scaled_upper=scaled_upper,
        scaled_abe_pass=scaled_abe_pass,
        rsabe_point_criterion=rsabe_point_criterion,
        rsabe_point_pass=rsabe_point_pass,
        analysis_note=note,
        subjects_df=subjects_df,
    )
