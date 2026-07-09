"""BE adapter: uploaded CSV -> BEStudy -> serializable dict."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from app.schemas.be import BeOptions, PowerRequest, SampleSizeRequest, SubjectRow
from openpkflow.be.methods import be_sample_size, be_tost_power
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
