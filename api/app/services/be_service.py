"""BE adapter: uploaded CSV -> BEStudy -> serializable dict."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from app.schemas.be import BeOptions, SubjectRow
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
