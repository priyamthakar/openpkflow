"""HTTP study inputs -> core StudyPipeline orchestration."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from app.schemas.pipeline import PipelineOptions
from openpkflow.pipeline import PipelineConfig, StudyPipeline, StudyPipelineResult


def run_pipeline(
    *,
    dissolution_path: Path | None,
    nca_path: Path | None,
    be_path: Path | None,
    input_names: dict[str, str],
    options: PipelineOptions,
) -> tuple[StudyPipelineResult, dict[str, Any]]:
    """Run configured uploaded stages and return the core result plus API payload."""
    config = PipelineConfig(
        title=options.title,
        dissolution_csv=dissolution_path,
        dissolution_reference=options.dissolution_reference,
        dissolution_test=options.dissolution_test,
        nca_csv=nca_path,
        nca_auc_method=options.nca_auc_method,
        nca_blq_method=options.nca_blq_method,
        be_csv=be_path,
        be_parameter=options.be_parameter,
        be_reference_col=options.be_reference_col,
        be_test_col=options.be_test_col,
        be_subject_col=options.be_subject_col,
        be_sequence_col=options.be_sequence_col,
        be_lower=options.be_lower,
        be_upper=options.be_upper,
    )
    result = StudyPipeline(config).run()
    payload = copy.deepcopy(result.to_dict())
    config_snapshot = payload["metadata"]["config"]
    for key, name in input_names.items():
        config_snapshot[key] = name
    payload["disclaimer"] = payload["metadata"]["disclaimer"]
    return result, payload
