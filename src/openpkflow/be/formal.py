"""Formal complete balanced 2x2 crossover bioequivalence ANOVA."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from scipy.stats import f as f_dist
from scipy.stats import t as t_dist

FormalDecision = Literal["PASS", "FAIL", "NOT_EVALUABLE"]


@dataclass(frozen=True)
class AnovaRow:
    """One source row from a formal crossover ANOVA table."""

    source: str
    df: int
    sum_squares: float
    mean_square: float | None
    f_value: float | None
    p_value: float | None


@dataclass
class FormalBEResult:
    """Result of a complete balanced 2x2 crossover ANOVA."""

    parameter: str
    n_subjects: int
    alpha: float
    confidence_level_pct: float
    be_lower: float
    be_upper: float
    treatment_log_lsmean: float
    reference_log_lsmean: float
    treatment_difference: float
    treatment_se: float
    residual_mse: float
    residual_df: int
    cv_intra_pct: float
    gmr: float
    gmr_lower_ci: float
    gmr_upper_ci: float
    decision: FormalDecision
    anova: list[AnovaRow]
    data: pd.DataFrame

    @property
    def bioequivalent(self) -> bool:
        """Return whether the formal decision is PASS."""
        return self.decision == "PASS"

    def summary(self) -> str:
        """Return an ASCII summary of the formal ANOVA result."""
        ci_label = f"{self.confidence_level_pct:g}% CI"
        return "\n".join(
            [
                "Formal 2x2 Crossover Bioequivalence ANOVA",
                "=" * 44,
                f"Parameter     : {self.parameter}",
                f"Subjects (n)  : {self.n_subjects}",
                f"GMR (T/R)     : {self.gmr:.4f}",
                f"{ci_label:<13}: [{self.gmr_lower_ci:.4f}, {self.gmr_upper_ci:.4f}]",
                f"Limits        : [{self.be_lower:.4f}, {self.be_upper:.4f}]",
                f"Residual MSE  : {self.residual_mse:.6g} (df={self.residual_df})",
                f"CV (intra)    : {self.cv_intra_pct:.1f}%",
                f"Decision      : {self.decision}",
            ]
        )

    def report(self, path: str | Path, format: str | None = None) -> None:
        """Write a formal ANOVA report as HTML or Markdown."""
        from openpkflow.be.formal_reporting import report_formal_be

        report_formal_be(self, path, format=format)


def formal_be_anova(
    data: pd.DataFrame,
    *,
    parameter: str,
    subject_col: str = "subject",
    sequence_col: str = "sequence",
    period_col: str = "period",
    treatment_col: str = "treatment",
    value_col: str | None = None,
    be_lower: float = 0.80,
    be_upper: float = 1.25,
    alpha: float = 0.05,
) -> FormalBEResult:
    """Fit a formal complete balanced TR/RT 2x2 crossover ANOVA.

    Parameters
    ----------
    data : pd.DataFrame
        Long-format complete crossover data.
    parameter : str
        Endpoint label used in result output.
    subject_col, sequence_col, period_col, treatment_col : str, optional
        Required design column names.
    value_col : str or None, optional
        Endpoint column. Defaults to ``parameter``.
    be_lower, be_upper : float, optional
        Ratio-scale acceptance limits.
    alpha : float, optional
        One-sided significance level.

    Returns
    -------
    FormalBEResult
        ANOVA table, treatment contrast, confidence interval, and decision.

    Raises
    ------
    ValueError
        If the data are not a complete balanced TR/RT 2x2 crossover design.

    References
    ----------
    FDA (2001) Statistical Approaches to Establishing Bioequivalence.
    Jones B, Kenward MG (2014) Design and Analysis of Cross-Over Trials.
    """
    endpoint = value_col or parameter
    _validate_limits(be_lower, be_upper, alpha)
    frame = _validate_complete_balanced_2x2(
        data,
        endpoint,
        subject_col,
        sequence_col,
        period_col,
        treatment_col,
    )

    subject_period = frame.pivot(index="subject", columns="period", values="log_value")
    subject_sequence = frame.drop_duplicates("subject").set_index("subject")["sequence"]
    sequence = subject_sequence.loc[subject_period.index]
    signs = np.where(sequence.to_numpy() == "TR", 1.0, -1.0)
    differences = subject_period[1].to_numpy() - subject_period[2].to_numpy()

    design = np.column_stack((np.ones(len(differences)), signs))
    coefficients, _, _, _ = np.linalg.lstsq(design, differences, rcond=None)
    period_difference, treatment_difference = (float(value) for value in coefficients)
    residual_difference = differences - design @ coefficients
    residual_ss = float(np.dot(residual_difference, residual_difference) / 2.0)
    residual_df = len(differences) - 2
    if residual_df <= 0:
        raise ValueError("A formal balanced 2x2 ANOVA requires at least four subjects.")
    residual_mse = residual_ss / residual_df

    subject_means = frame.groupby("subject", sort=False)["log_value"].mean()
    sequence_means = frame.groupby("sequence", sort=False)["log_value"].mean()
    grand_mean = float(frame["log_value"].mean())
    n_per_sequence = sequence.value_counts()
    sequence_ss = float(
        2.0
        * sum(
            n_per_sequence[name] * (mean - grand_mean) ** 2 for name, mean in sequence_means.items()
        )
    )
    subject_within_sequence_ss = float(
        2.0
        * sum(
            (subject_means[subject] - sequence_means[subject_sequence[subject]]) ** 2
            for subject in subject_means.index
        )
    )
    period_ss = float(len(differences) * period_difference**2 / 2.0)
    treatment_ss = float(len(differences) * treatment_difference**2 / 2.0)
    subject_within_sequence_df = len(differences) - 2
    subject_within_sequence_ms = subject_within_sequence_ss / subject_within_sequence_df

    treatment_se = math.sqrt(2.0 * residual_mse / len(differences))
    critical = float(t_dist.ppf(1.0 - alpha, residual_df))
    lower_log = treatment_difference - critical * treatment_se
    upper_log = treatment_difference + critical * treatment_se
    gmr = math.exp(treatment_difference)
    lower_ci = math.exp(lower_log)
    upper_ci = math.exp(upper_log)
    decision: FormalDecision = "PASS" if lower_ci >= be_lower and upper_ci <= be_upper else "FAIL"

    t_lsmean = float(frame.loc[frame["treatment"] == "T", "log_value"].mean())
    r_lsmean = float(frame.loc[frame["treatment"] == "R", "log_value"].mean())
    anova = [
        _anova_row(
            "Sequence",
            1,
            sequence_ss,
            subject_within_sequence_ms,
            subject_within_sequence_df,
        ),
        _anova_row(
            "Subject within sequence",
            subject_within_sequence_df,
            subject_within_sequence_ss,
            residual_mse,
            residual_df,
        ),
        _anova_row("Period", 1, period_ss, residual_mse, residual_df),
        _anova_row("Treatment", 1, treatment_ss, residual_mse, residual_df),
        AnovaRow("Residual", residual_df, residual_ss, residual_mse, None, None),
    ]
    return FormalBEResult(
        parameter=parameter,
        n_subjects=len(differences),
        alpha=alpha,
        confidence_level_pct=(1.0 - 2.0 * alpha) * 100.0,
        be_lower=be_lower,
        be_upper=be_upper,
        treatment_log_lsmean=t_lsmean,
        reference_log_lsmean=r_lsmean,
        treatment_difference=treatment_difference,
        treatment_se=treatment_se,
        residual_mse=residual_mse,
        residual_df=residual_df,
        cv_intra_pct=math.sqrt(math.exp(residual_mse) - 1.0) * 100.0,
        gmr=gmr,
        gmr_lower_ci=lower_ci,
        gmr_upper_ci=upper_ci,
        decision=decision,
        anova=anova,
        data=frame.drop(columns="log_value"),
    )


def _anova_row(
    source: str,
    df: int,
    sum_squares: float,
    denominator_ms: float,
    denominator_df: int,
) -> AnovaRow:
    mean_square = sum_squares / df
    f_value = mean_square / denominator_ms if denominator_ms > 0.0 else None
    p_value = float(f_dist.sf(f_value, df, denominator_df)) if f_value is not None else None
    return AnovaRow(source, df, sum_squares, mean_square, f_value, p_value)


def _validate_limits(be_lower: float, be_upper: float, alpha: float) -> None:
    if not 0.0 < be_lower < be_upper:
        raise ValueError("be_lower must be positive and less than be_upper.")
    if not 0.0 < alpha < 0.5:
        raise ValueError("alpha must be in (0, 0.5).")


def _validate_complete_balanced_2x2(
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
        raise ValueError(f"Missing required formal BE columns: {missing!r}.")
    frame = data[required].copy()
    frame.columns = ["subject", "sequence", "period", "treatment", "value"]
    if frame.isna().any().any():
        raise ValueError("Formal BE data must not contain missing values.")
    frame["sequence"] = frame["sequence"].astype(str).str.upper()
    frame["treatment"] = frame["treatment"].astype(str).str.upper()
    frame["period"] = pd.to_numeric(frame["period"], errors="coerce")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    if not np.isfinite(frame["period"]).all() or not np.isfinite(frame["value"]).all():
        raise ValueError("Formal BE periods and endpoint values must be finite.")
    if (frame["value"] <= 0.0).any():
        raise ValueError("Formal BE endpoint values must be > 0 for log analysis.")
    if not set(frame["sequence"]) == {"TR", "RT"}:
        raise ValueError("Formal balanced 2x2 ANOVA requires both TR and RT sequences.")
    if not set(frame["period"]) == {1, 2}:
        raise ValueError("Formal balanced 2x2 ANOVA requires periods 1 and 2.")
    if not set(frame["treatment"]) == {"T", "R"}:
        raise ValueError("Formal balanced 2x2 ANOVA requires treatments T and R.")
    if frame.duplicated(["subject", "period"]).any():
        raise ValueError("Formal BE data must contain one observation per subject and period.")
    subject_counts = frame.groupby("subject", sort=False).size()
    if not (subject_counts == 2).all():
        raise ValueError("Formal balanced 2x2 ANOVA requires complete two-period subjects.")
    sequence_per_subject = frame.groupby("subject", sort=False)["sequence"].nunique()
    if not (sequence_per_subject == 1).all():
        raise ValueError("Each subject must have exactly one sequence assignment.")
    expected = {"TR": {1: "T", 2: "R"}, "RT": {1: "R", 2: "T"}}
    for row in frame.itertuples(index=False):
        if expected[row.sequence].get(int(row.period)) != row.treatment:
            raise ValueError("Treatment assignments must agree with sequence and period.")
    sequence_counts = frame.groupby("sequence", sort=False)["subject"].nunique()
    if sequence_counts["TR"] != sequence_counts["RT"]:
        raise ValueError("Formal initial release supports balanced TR/RT sequence allocation only.")
    if sequence_counts["TR"] < 2:
        raise ValueError("Formal balanced 2x2 ANOVA requires at least two subjects per sequence.")
    frame["log_value"] = np.log(frame["value"])
    return frame
