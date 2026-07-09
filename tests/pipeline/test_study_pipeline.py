"""Tests for the end-to-end StudyPipeline orchestration layer."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from openpkflow import __version__
from openpkflow.datasets import example_similar_path, example_theoph_path
from openpkflow.pipeline import (
    PipelineConfig,
    StudyPipeline,
    StudyPipelineResult,
    load_pipeline_config,
)

_DISCLAIMER_SNIPPET = (
    "This report was generated using OpenPKFlow (open-source). Final regulatory "
    "interpretation should be reviewed by qualified formulation, pharmacokinetic, "
    "and regulatory experts."
)


def test_empty_config_raises_clear_value_error() -> None:
    """Empty config (no stage inputs) must raise ValueError with a clear message."""
    cfg = PipelineConfig()
    with pytest.raises(ValueError, match="no stages enabled"):
        cfg.validate()
    with pytest.raises(ValueError, match="no stages enabled"):
        StudyPipeline(PipelineConfig())


def test_dissolution_only_pipeline() -> None:
    """Dissolution-only pipeline on example_similar.csv.

    Reference: FDA 1997 dissolution guidance f2 similarity threshold;
    bundled example_similar profile yields f2 well above 50.
    """
    cfg = PipelineConfig(
        title="Dissolution-only test",
        dissolution_csv=Path(example_similar_path()),
        dissolution_reference="reference",
        dissolution_test="test",
    )
    result = StudyPipeline(cfg).run()

    assert result.dissolution is not None
    assert result.nca is None
    assert result.be is None
    assert result.dissolution.f2_value >= 50.0
    assert result.metadata["stages_completed"] == ["dissolution"]
    assert result.metadata["stage_status"]["dissolution"] == "completed"
    assert result.metadata["openpkflow_version"] == __version__
    assert "generated_at_utc" in result.metadata


def test_nca_only_pipeline() -> None:
    """NCA-only pipeline on theoph.csv (R nlme::Theoph, 12 subjects).

    Cross-validated elsewhere against PKNCA 0.12.1 (Denney et al., 2015).
    """
    cfg = PipelineConfig(
        title="NCA-only test",
        nca_csv=Path(example_theoph_path()),
        nca_auc_method="linear_up_log_down",
        nca_blq_method="none",
    )
    result = StudyPipeline(cfg).run()

    assert result.nca is not None
    assert result.dissolution is None
    assert result.be is None
    assert len(result.nca.results) == 12
    assert result.nca.auc_method == "linear_up_log_down"
    assert result.nca.blq_method == "none"
    assert result.metadata["stages_completed"] == ["nca"]
    assert result.metadata["methods"]["nca_auc_method"] == "linear_up_log_down"


def test_multi_stage_dissolution_and_nca() -> None:
    """Multi-stage pipeline: dissolution + NCA when both CSVs are provided."""
    cfg = PipelineConfig(
        title="Multi-stage test",
        dissolution_csv=Path(example_similar_path()),
        dissolution_reference="reference",
        dissolution_test="test",
        nca_csv=Path(example_theoph_path()),
        nca_auc_method="linear_up_log_down",
        nca_blq_method="none",
    )
    result = StudyPipeline(cfg).run()

    assert result.dissolution is not None
    assert result.nca is not None
    assert set(result.metadata["stages_completed"]) == {"dissolution", "nca"}
    text = result.summary()
    assert "Dissolution Similarity Analysis" in text or "f2" in text
    assert "NCA" in text or "AUClast" in text
    assert _DISCLAIMER_SNIPPET.split(".")[0] in text


def test_be_stage_with_temp_csv(tmp_path: Path) -> None:
    """BE stage on a synthetic wide-format CSV (paired TOST).

    GMR near 1.0 with modest noise should be bioequivalent at 80-125% limits.
    """
    be_csv = tmp_path / "be_wide.csv"
    n = 12
    subjects = [f"S{i}" for i in range(1, n + 1)]
    ref = [100.0 + (i % 5) for i in range(n)]
    tst = [r * 1.02 for r in ref]
    pd.DataFrame(
        {
            "subject": subjects,
            "sequence": ["RT", "TR"] * (n // 2),
            "reference": ref,
            "test": tst,
        }
    ).to_csv(be_csv, index=False)

    cfg = PipelineConfig(
        title="BE-only test",
        be_csv=be_csv,
        be_parameter="AUCinf",
        be_lower=0.80,
        be_upper=1.25,
    )
    result = StudyPipeline(cfg).run()
    assert result.be is not None
    assert result.be.n == n
    assert result.be.bioequivalent is True
    assert result.metadata["stages_completed"] == ["be"]


def test_report_html_contains_disclaimer_and_version(tmp_path: Path) -> None:
    """HTML pipeline report must include disclaimer text and package version."""
    cfg = PipelineConfig(
        title="Report HTML test",
        dissolution_csv=Path(example_similar_path()),
        dissolution_reference="reference",
        dissolution_test="test",
    )
    result = StudyPipeline(cfg).run()
    out = tmp_path / "pipeline_report.html"
    written = result.report(out)

    assert written.is_file()
    html = written.read_text(encoding="utf-8")
    assert _DISCLAIMER_SNIPPET in html
    assert __version__ in html
    assert "OpenPKFlow" in html
    assert "Dissolution" in html


def test_report_markdown(tmp_path: Path) -> None:
    """Markdown report path is supported and includes disclaimer."""
    cfg = PipelineConfig(
        title="Report MD test",
        nca_csv=Path(example_theoph_path()),
        nca_auc_method="linear",
        nca_blq_method="none",
    )
    result = StudyPipeline(cfg).run()
    out = tmp_path / "pipeline_report.md"
    written = result.report(out)
    text = written.read_text(encoding="utf-8")
    assert _DISCLAIMER_SNIPPET in text
    assert __version__ in text
    assert "Non-Compartmental Analysis" in text


def test_to_dict_json_serializable() -> None:
    """to_dict() must be JSON-serializable for CLI --json export."""
    cfg = PipelineConfig(
        dissolution_csv=Path(example_similar_path()),
        dissolution_reference="reference",
        dissolution_test="test",
    )
    result = StudyPipeline(cfg).run()
    payload = result.to_dict()
    encoded = json.dumps(payload, default=str)
    assert "dissolution" in encoded
    assert "metadata" in encoded
    assert payload["dissolution"] is not None
    assert payload["dissolution"]["f2_value"] == result.dissolution.f2_value  # type: ignore[union-attr]


def test_load_pipeline_config_json(tmp_path: Path) -> None:
    """JSON config loading resolves relative paths against the config directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    src = Path(example_similar_path())
    dest = data_dir / "diss.csv"
    dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(
        json.dumps(
            {
                "title": "From JSON",
                "dissolution_csv": "data/diss.csv",
                "dissolution_reference": "reference",
                "dissolution_test": "test",
            }
        ),
        encoding="utf-8",
    )
    cfg = load_pipeline_config(cfg_path)
    assert cfg.title == "From JSON"
    assert cfg.dissolution_csv is not None
    assert cfg.dissolution_csv.is_file()
    result = StudyPipeline(cfg).run()
    assert isinstance(result, StudyPipelineResult)
    assert result.dissolution is not None


def test_dissolution_missing_labels_raises() -> None:
    """dissolution_csv without reference/test labels must fail validation."""
    with pytest.raises(ValueError, match="dissolution_reference"):
        PipelineConfig(
            dissolution_csv=Path(example_similar_path()),
        ).validate()


def test_failed_stage_not_silent(tmp_path: Path) -> None:
    """Missing CSV path must raise FileNotFoundError (not swallowed)."""
    missing = tmp_path / "does_not_exist.csv"
    cfg = PipelineConfig(
        nca_csv=missing,
        nca_auc_method="linear_up_log_down",
        nca_blq_method="none",
    )
    with pytest.raises(FileNotFoundError, match="nca_csv"):
        StudyPipeline(cfg).run()
