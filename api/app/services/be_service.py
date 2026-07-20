"""BE adapter: uploaded CSV -> BEStudy -> serializable dict."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from app.schemas.be import (
    BeOptions,
    FormalBeOptions,
    PowerRequest,
    RsabeOptions,
    SampleSizeRequest,
    SubjectRow,
)
from openpkflow.be.formal import formal_be_anova
from openpkflow.be.methods import be_sample_size, be_tost_power
from openpkflow.be.rsabe import fda_partial_replicate_rsabe
from openpkflow.be.study import BEStudy

_DISCLAIMER = (
    "This report was generated using OpenPKFlow (open-source). Final regulatory "
    "interpretation should be reviewed by qualified formulation, pharmacokinetic, "
    "and regulatory experts."
)


def _load_df(path: Path, opts: BeOptions) -> pd.DataFrame:
    df = pd.read_csv(path)
    if opts.columns:
        df = df.rename(columns=opts.columns)
    return df


def run_be(path: Path, opts: BeOptions) -> dict[str, Any]:
    df = _load_df(path, opts)
    study = BEStudy(
        df,
        parameter=opts.parameter,
        reference_col=opts.reference_col,
        test_col=opts.test_col,
        subject_col=opts.subject_col,
        sequence_col=opts.sequence_col,
    )
    result = study.analyze(be_lower=opts.be_lower, be_upper=opts.be_upper, alpha=opts.alpha)

    has_sequence = "sequence" in result.subjects_df.columns
    subjects: list[dict[str, Any]] = []
    for _, row in result.subjects_df.iterrows():
        subjects.append(
            SubjectRow(
                subject=str(row["subject"]),
                reference=float(row["reference"]),
                test=float(row["test"]),
                ratio=float(row["ratio"]),
                log_diff=float(row["log_diff"]),
                sequence=str(row["sequence"]) if has_sequence else None,
            ).model_dump()
        )

    return {
        "parameter": result.parameter,
        "n": result.n,
        "gmr": float(result.gmr),
        "gmr_lower_90ci": float(result.gmr_lower_90ci),
        "gmr_upper_90ci": float(result.gmr_upper_90ci),
        "be_lower": float(result.be_lower),
        "be_upper": float(result.be_upper),
        "bioequivalent": bool(result.bioequivalent),
        "cv_intra_pct": float(result.cv_intra_pct),
        "subjects": subjects,
        "disclaimer": _DISCLAIMER,
    }


def write_be_report(path: Path, opts: BeOptions, out_path: Path, fmt: str) -> None:
    df = _load_df(path, opts)
    study = BEStudy(
        df,
        parameter=opts.parameter,
        reference_col=opts.reference_col,
        test_col=opts.test_col,
        subject_col=opts.subject_col,
        sequence_col=opts.sequence_col,
    )
    result = study.analyze(be_lower=opts.be_lower, be_upper=opts.be_upper, alpha=opts.alpha)
    result.report(out_path, format=fmt)


def run_formal_be(path: Path, opts: FormalBeOptions) -> dict[str, Any]:
    df = pd.read_csv(path)
    if opts.columns:
        df = df.rename(columns=opts.columns)
    result = formal_be_anova(
        df,
        parameter=opts.parameter,
        subject_col=opts.subject_col,
        sequence_col=opts.sequence_col,
        period_col=opts.period_col,
        treatment_col=opts.treatment_col,
        value_col=opts.value_col,
        be_lower=opts.be_lower,
        be_upper=opts.be_upper,
        alpha=opts.alpha,
    )
    return {
        "parameter": result.parameter,
        "design": "complete_balanced_2x2",
        "n_subjects": result.n_subjects,
        "alpha": result.alpha,
        "confidence_level_pct": result.confidence_level_pct,
        "be_lower": result.be_lower,
        "be_upper": result.be_upper,
        "treatment_log_lsmean": result.treatment_log_lsmean,
        "reference_log_lsmean": result.reference_log_lsmean,
        "treatment_difference": result.treatment_difference,
        "treatment_se": result.treatment_se,
        "residual_mse": result.residual_mse,
        "residual_df": result.residual_df,
        "cv_intra_pct": result.cv_intra_pct,
        "gmr": result.gmr,
        "gmr_lower_ci": result.gmr_lower_ci,
        "gmr_upper_ci": result.gmr_upper_ci,
        "decision": result.decision,
        "anova": [row.__dict__ for row in result.anova],
        "disclaimer": _DISCLAIMER,
    }


def write_formal_be_report(path: Path, opts: FormalBeOptions, out_path: Path, fmt: str) -> None:
    df = pd.read_csv(path)
    if opts.columns:
        df = df.rename(columns=opts.columns)
    result = formal_be_anova(
        df,
        parameter=opts.parameter,
        subject_col=opts.subject_col,
        sequence_col=opts.sequence_col,
        period_col=opts.period_col,
        treatment_col=opts.treatment_col,
        value_col=opts.value_col,
        be_lower=opts.be_lower,
        be_upper=opts.be_upper,
        alpha=opts.alpha,
    )
    result.report(out_path, format=fmt)


def run_rsabe(path: Path, opts: RsabeOptions) -> dict[str, Any]:
    df = pd.read_csv(path)
    if opts.columns:
        df = df.rename(columns=opts.columns)
    result = fda_partial_replicate_rsabe(
        df,
        parameter=opts.parameter,
        subject_col=opts.subject_col,
        sequence_col=opts.sequence_col,
        period_col=opts.period_col,
        treatment_col=opts.treatment_col,
        value_col=opts.value_col,
        alpha=opts.alpha,
        sigma_wr_floor=opts.sigma_wr_floor,
        highly_variable_cv_pct=opts.highly_variable_cv_pct,
    )
    return {
        "parameter": result.parameter,
        "decision": result.decision,
        "design": result.design,
        "jurisdiction": result.jurisdiction,
        "validation_status": result.validation_status,
        "message": result.message,
        "n_subjects": result.n_subjects,
        "alpha": result.alpha,
        "confidence_level_pct": result.confidence_level_pct,
        "delta_hat": result.delta_hat,
        "delta_ci_lower": result.delta_ci_lower,
        "delta_ci_upper": result.delta_ci_upper,
        "gmr": result.gmr,
        "gmr_ci_lower": result.gmr_ci_lower,
        "gmr_ci_upper": result.gmr_ci_upper,
        "sigma_wr": result.sigma_wr,
        "sigma_wr_ci_lower": result.sigma_wr_ci_lower,
        "sigma_wr_ci_upper": result.sigma_wr_ci_upper,
        "cv_wr_pct": result.cv_wr_pct,
        "highly_variable": result.highly_variable,
        "theta": result.theta,
        "aggregate_criterion_point": result.aggregate_criterion_point,
        "aggregate_criterion_upper": result.aggregate_criterion_upper,
        "point_estimate_constraint_met": result.point_estimate_constraint_met,
        "disclaimer": _DISCLAIMER,
    }


def write_rsabe_report(path: Path, opts: RsabeOptions, out_path: Path, fmt: str) -> None:
    df = pd.read_csv(path)
    if opts.columns:
        df = df.rename(columns=opts.columns)
    result = fda_partial_replicate_rsabe(
        df,
        parameter=opts.parameter,
        subject_col=opts.subject_col,
        sequence_col=opts.sequence_col,
        period_col=opts.period_col,
        treatment_col=opts.treatment_col,
        value_col=opts.value_col,
        alpha=opts.alpha,
        sigma_wr_floor=opts.sigma_wr_floor,
        highly_variable_cv_pct=opts.highly_variable_cv_pct,
    )
    result.report(out_path, format=fmt)


def run_be_power(req: PowerRequest) -> dict[str, Any]:
    power = be_tost_power(
        req.gmr,
        req.cv,
        req.n,
        be_lower=req.be_lower,
        be_upper=req.be_upper,
        alpha=req.alpha,
    )
    return {
        "power": float(power),
        "gmr": float(req.gmr),
        "cv": float(req.cv),
        "n": int(req.n),
        "be_lower": float(req.be_lower),
        "be_upper": float(req.be_upper),
        "alpha": float(req.alpha),
        "disclaimer": _DISCLAIMER,
    }


def run_be_sample_size(req: SampleSizeRequest) -> dict[str, Any]:
    try:
        n, achieved = be_sample_size(
            req.gmr,
            req.cv,
            req.target_power,
            be_lower=req.be_lower,
            be_upper=req.be_upper,
            alpha=req.alpha,
            max_n=req.max_n,
        )
    except RuntimeError as exc:
        raise ValueError(str(exc)) from exc
    return {
        "n": int(n),
        "achieved_power": float(achieved),
        "gmr": float(req.gmr),
        "cv": float(req.cv),
        "target_power": float(req.target_power),
        "be_lower": float(req.be_lower),
        "be_upper": float(req.be_upper),
        "alpha": float(req.alpha),
        "disclaimer": _DISCLAIMER,
    }
