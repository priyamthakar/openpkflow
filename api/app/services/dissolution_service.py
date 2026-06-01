"""Dissolution adapter: HTTP payload -> DissolutionStudy -> serializable dict."""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

from app.schemas.dissolution import DissolutionColumns
from openpkflow.dissolution.loader import DissolutionCSVConfig
from openpkflow.dissolution.study import DissolutionStudy

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
