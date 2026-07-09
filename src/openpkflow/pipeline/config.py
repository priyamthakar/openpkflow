"""Pipeline configuration loading (JSON primary; YAML optional if PyYAML installed)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any


@dataclass
class PipelineConfig:
    """Configuration for an end-to-end OpenPKFlow study pipeline.

    Only stages with inputs provided are run. AUC and BLQ methods for NCA
    are always explicit (no silent defaults beyond these named fields).

    Parameters
    ----------
    title : str, optional
        Report title. Default ``"OpenPKFlow Study Report"``.
    dissolution_csv : Path or None, optional
        Path to dissolution CSV for f1/f2 comparison.
    dissolution_reference : str or None, optional
        Reference formulation label.
    dissolution_test : str or None, optional
        Test formulation label.
    nca_csv : Path or None, optional
        Path to NCA concentration-time CSV.
    nca_auc_method : str, optional
        AUC method: ``"linear"``, ``"log"``, or ``"linear_up_log_down"``.
    nca_blq_method : str, optional
        BLQ handling method identifier (e.g. ``"none"``).
    be_csv : Path or None, optional
        Path to wide-format BE CSV (subject, reference, test[, sequence]).
    be_parameter : str, optional
        PK parameter label for BE output. Default ``"AUCinf"``.
    be_reference_col : str, optional
        Column name for reference values. Default ``"reference"``.
    be_test_col : str, optional
        Column name for test values. Default ``"test"``.
    be_subject_col : str, optional
        Column name for subject IDs. Default ``"subject"``.
    be_sequence_col : str or None, optional
        Column name for sequence (RT/TR), or None if absent.
    be_lower : float, optional
        Lower BE acceptance limit. Default 0.80.
    be_upper : float, optional
        Upper BE acceptance limit. Default 1.25.
    """

    title: str = "OpenPKFlow Study Report"
    dissolution_csv: Path | None = None
    dissolution_reference: str | None = None
    dissolution_test: str | None = None
    nca_csv: Path | None = None
    nca_auc_method: str = "linear_up_log_down"
    nca_blq_method: str = "none"
    be_csv: Path | None = None
    be_parameter: str = "AUCinf"
    be_reference_col: str = "reference"
    be_test_col: str = "test"
    be_subject_col: str = "subject"
    be_sequence_col: str | None = "sequence"
    be_lower: float = 0.80
    be_upper: float = 1.25

    def enabled_stages(self) -> list[str]:
        """Return names of stages that have sufficient inputs to run.

        Returns
        -------
        list[str]
            Subset of ``\"dissolution\"``, ``\"nca\"``, ``\"be\"``.
        """
        stages: list[str] = []
        if self.dissolution_csv is not None:
            stages.append("dissolution")
        if self.nca_csv is not None:
            stages.append("nca")
        if self.be_csv is not None:
            stages.append("be")
        return stages

    def validate(self) -> None:
        """Validate that at least one stage is configured and options are consistent.

        Raises
        ------
        ValueError
            If no stages are configured, or dissolution lacks reference/test labels.
        """
        stages = self.enabled_stages()
        if not stages:
            raise ValueError(
                "PipelineConfig has no stages enabled. Provide at least one of: "
                "dissolution_csv, nca_csv, or be_csv."
            )
        if self.dissolution_csv is not None and (
            not self.dissolution_reference or not self.dissolution_test
        ):
            raise ValueError("dissolution_csv requires dissolution_reference and dissolution_test.")
        valid_auc = ("linear", "log", "linear_up_log_down")
        if self.nca_csv is not None and self.nca_auc_method not in valid_auc:
            raise ValueError(
                f"nca_auc_method must be one of {valid_auc!r} (got {self.nca_auc_method!r})."
            )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable snapshot of this config.

        Returns
        -------
        dict[str, Any]
            Paths as strings (or None).
        """
        raw = asdict(self)
        out: dict[str, Any] = {}
        for key, value in raw.items():
            if isinstance(value, Path):
                out[key] = str(value)
            else:
                out[key] = value
        return out

    @classmethod
    def from_dict(cls, data: dict[str, Any], *, base_dir: Path | None = None) -> PipelineConfig:
        """Build a PipelineConfig from a plain dict.

        Parameters
        ----------
        data : dict
            Config keys matching PipelineConfig fields. Unknown keys are ignored.
        base_dir : Path or None, optional
            Resolve relative path fields against this directory.

        Returns
        -------
        PipelineConfig
            Validated configuration instance.

        Raises
        ------
        ValueError
            If the resulting config fails :meth:`validate`.
        """
        known = {f.name for f in fields(cls)}
        kwargs: dict[str, Any] = {}
        path_fields = {
            "dissolution_csv",
            "nca_csv",
            "be_csv",
        }
        for key, value in data.items():
            if key not in known:
                continue
            if key in path_fields and value is not None:
                p = Path(str(value))
                if not p.is_absolute() and base_dir is not None:
                    p = (base_dir / p).resolve()
                kwargs[key] = p
            else:
                kwargs[key] = value
        cfg = cls(**kwargs)
        cfg.validate()
        return cfg


def load_pipeline_config(path: str | Path) -> PipelineConfig:
    """Load a PipelineConfig from a JSON or YAML file.

    JSON is always supported. YAML (``.yaml`` / ``.yml``) requires PyYAML;
    if PyYAML is not installed, a clear ImportError message is raised.

    Parameters
    ----------
    path : str or Path
        Path to the config file.

    Returns
    -------
    PipelineConfig
        Loaded and validated configuration.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If the file cannot be parsed or fails validation.
    ImportError
        If a YAML file is requested but PyYAML is not installed.
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Pipeline config not found: {p}")

    text = p.read_text(encoding="utf-8")
    suffix = p.suffix.lower()
    data: dict[str, Any]

    if suffix in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "YAML config requires PyYAML. Install with `pip install pyyaml`, "
                "or use a JSON config file instead."
            ) from exc
        loaded = yaml.safe_load(text)
        if not isinstance(loaded, dict):
            raise ValueError(f"YAML config must be a mapping/object (got {type(loaded).__name__}).")
        data = loaded
    else:
        # Default: JSON (including .json and extension-less / unknown)
        try:
            loaded = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON pipeline config {p}: {exc}") from exc
        if not isinstance(loaded, dict):
            raise ValueError(f"JSON config must be an object (got {type(loaded).__name__}).")
        data = loaded

    return PipelineConfig.from_dict(data, base_dir=p.parent.resolve())
