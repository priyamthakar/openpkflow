"""Dissolution adapter: HTTP payload -> DissolutionStudy -> serializable dict."""

from __future__ import annotations

import tempfile
import warnings
from pathlib import Path
from typing import Any

import pandas as pd

from app.schemas.dissolution import DissolutionColumns, MultiMediaRequest, WorkbenchRequest
from openpkflow.dissolution.loader import DissolutionCSVConfig
from openpkflow.dissolution.multi_media import MultiMediaStudy
from openpkflow.dissolution.study import DissolutionStudy
from openpkflow.dissolution.workbench import (
    DissolutionWorkbenchConfig,
    DissolutionWorkbenchResult,
    run_dissolution_workbench,
)

_DISCLAIMER = (
    "This report was generated using OpenPKFlow (open-source). Final regulatory "
    "interpretation should be reviewed by qualified formulation, pharmacokinetic, "
    "and regulatory experts."
)


def _config(columns: DissolutionColumns) -> DissolutionCSVConfig:
    return DissolutionCSVConfig(
        formulation_col=columns.formulation,
        batch_col=columns.batch,
        time_col=columns.time,
        percent_released_col=columns.percent_released,
    )


def get_formulations(path: Path, columns: DissolutionColumns) -> list[str]:
    study = DissolutionStudy.from_csv(path, _config(columns))
    return study.formulations()


def run_compare(
    path: Path,
    columns: DissolutionColumns,
    reference: str,
    test: str,
) -> dict[str, Any]:
    cfg = _config(columns)
    study = DissolutionStudy.from_csv(path, cfg)

    user_warnings: list[str] = []
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = study.compare(reference, test)
    for w in caught:
        user_warnings.append(str(w.message))

    d = result.to_dict()
    d["similar"] = result.f2_value >= 50.0
    d["warnings"] = user_warnings
    d["disclaimer"] = _DISCLAIMER
    return d


def write_dissolution_report(
    path: Path,
    columns: DissolutionColumns,
    reference: str,
    test: str,
    out_path: Path,
    fmt: str,
) -> None:
    cfg = _config(columns)
    study = DissolutionStudy.from_csv(path, cfg)
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        result = study.compare(reference, test)
    result.report(out_path, format=fmt)


def _write_media_csvs(req: MultiMediaRequest, tmp_dir: Path) -> dict[str, Path]:
    media_csvs: dict[str, Path] = {}
    for i, medium in enumerate(req.media):
        path = tmp_dir / f"media_{i}.csv"
        df = pd.DataFrame([row.model_dump() for row in medium.rows])
        df.to_csv(path, index=False)
        media_csvs[medium.name] = path
    return media_csvs


def run_multi_media(req: MultiMediaRequest) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp:
        media_csvs = _write_media_csvs(req, Path(tmp))
        study = MultiMediaStudy(
            media_csvs,
            reference_label=req.reference_label,
            test_label=req.test_label,
        )
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = study.run()

        per_media = []
        for medium in result.media_names:
            cr = result.per_media_results[medium]
            per_media.append(
                {
                    "medium": medium,
                    "f1_value": float(cr.f1_value),
                    "f2_value": float(cr.f2_value),
                    "similar": bool(cr.f2_value >= 50.0),
                    "n_timepoints": int(cr.n_timepoints),
                    "time_points": list(cr.time_points),
                    "reference_mean": list(cr.reference_mean),
                    "test_mean": list(cr.test_mean),
                }
            )

        return {
            "reference_label": result.reference_label,
            "test_label": result.test_label,
            "media_names": list(result.media_names),
            "f2_summary": {k: float(v) for k, v in result.f2_summary.items()},
            "overall_pass": bool(result.overall_pass),
            "per_media": per_media,
            "disclaimer": _DISCLAIMER,
        }


def write_multi_media_report(req: MultiMediaRequest, out_path: Path, fmt: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        media_csvs = _write_media_csvs(req, Path(tmp))
        study = MultiMediaStudy(
            media_csvs,
            reference_label=req.reference_label,
            test_label=req.test_label,
        )
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = study.run()
        result.report(out_path, format=fmt)  # type: ignore[arg-type]


def _workbench_result(req: WorkbenchRequest) -> DissolutionWorkbenchResult:
    config = DissolutionWorkbenchConfig(**req.config.model_dump())
    data = pd.DataFrame([row.model_dump() for row in req.rows])
    try:
        return run_dissolution_workbench(data, config)
    except RuntimeError as exc:
        raise ValueError(str(exc)) from exc


def run_workbench(req: WorkbenchRequest) -> dict[str, Any]:
    return _workbench_result(req).to_dict()


def write_workbench_report(
    req: WorkbenchRequest,
    out_path: Path,
    fmt: str,
) -> None:
    result = _workbench_result(req)
    result.report(out_path, format=fmt)  # type: ignore[arg-type]


def write_workbench_audit_bundle(
    req: WorkbenchRequest,
    out_path: Path,
) -> None:
    _workbench_result(req).audit_bundle(out_path)
