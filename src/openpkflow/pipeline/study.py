"""End-to-end study pipeline orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from openpkflow import __version__
from openpkflow.be.results import BEResult
from openpkflow.dissolution.study import ComparisonResult
from openpkflow.nca.results import NCASummaryResults
from openpkflow.pipeline.config import PipelineConfig

_DISCLAIMER = (
    "This report was generated using OpenPKFlow (open-source). Final regulatory "
    "interpretation should be reviewed by qualified formulation, pharmacokinetic, "
    "and regulatory experts."
)


@dataclass
class StudyPipelineResult:
    """Aggregated result of a multi-stage study pipeline.

    Parameters
    ----------
    dissolution : ComparisonResult or None
        Dissolution f1/f2 comparison result when the stage ran.
    nca : NCASummaryResults or None
        NCA summary when the stage ran.
    be : BEResult or None
        Bioequivalence result when the stage ran.
    metadata : dict
        Audit metadata: version, timestamp, config snapshot, stage status, warnings.
    """

    dissolution: ComparisonResult | None = None
    nca: NCASummaryResults | None = None
    be: BEResult | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        """Return an ASCII multi-section pipeline summary.

        Returns
        -------
        str
            Human-readable summary of all completed stages and metadata.
        """
        title = str(self.metadata.get("title", "OpenPKFlow Study Report"))
        lines = [
            title,
            "=" * max(len(title), 40),
            f"OpenPKFlow version : {self.metadata.get('openpkflow_version', __version__)}",
            f"Generated (UTC)    : {self.metadata.get('generated_at_utc', '')}",
            (
                "Stages requested   : "
                f"{', '.join(self.metadata.get('stages_requested', [])) or 'none'}"
            ),
            (
                "Stages completed   : "
                f"{', '.join(self.metadata.get('stages_completed', [])) or 'none'}"
            ),
            "",
        ]

        stage_status = self.metadata.get("stage_status", {})
        if stage_status:
            lines.append("Stage status")
            lines.append("-" * 12)
            for name, status in stage_status.items():
                lines.append(f"  {name:<14}: {status}")
            lines.append("")

        warnings = self.metadata.get("warnings", [])
        if warnings:
            lines.append("Warnings")
            lines.append("-" * 8)
            for w in warnings:
                lines.append(f"  - {w}")
            lines.append("")

        if self.dissolution is not None:
            lines.append(self.dissolution.summary())
            lines.append("")

        if self.nca is not None:
            lines.append("NCA Summary")
            lines.append("===========")
            lines.append(self.nca.summary())
            lines.append("")

        if self.be is not None:
            lines.append(self.be.summary())
            lines.append("")

        lines.append("Disclaimer")
        lines.append("----------")
        lines.append(_DISCLAIMER)
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Serialize pipeline results and metadata to a JSON-friendly dict.

        Returns
        -------
        dict[str, Any]
            Nested dict with dissolution/nca/be sections and metadata.
        """
        out: dict[str, Any] = {
            "metadata": dict(self.metadata),
            "dissolution": None,
            "nca": None,
            "be": None,
        }

        if self.dissolution is not None:
            d = self.dissolution
            out["dissolution"] = {
                "reference_label": d.reference_label,
                "test_label": d.test_label,
                "f1_value": d.f1_value,
                "f2_value": d.f2_value,
                "n_timepoints": d.n_timepoints,
                "time_points": list(d.time_points),
                "reference_mean": list(d.reference_mean),
                "test_mean": list(d.test_mean),
                "f2_method": getattr(d, "f2_method", "regulatory"),
                "warnings": list(getattr(d, "warnings", [])),
            }

        if self.nca is not None:
            df = self.nca.to_dataframe()
            # Convert non-JSON types (numpy, Path, etc.) via Python natives
            records = df.where(df.notna(), other=None).to_dict(orient="records")
            out["nca"] = {
                "study_label": self.nca.study_label,
                "auc_method": self.nca.auc_method,
                "blq_method": self.nca.blq_method,
                "n_subjects": len(self.nca.results),
                "subjects": records,
            }

        if self.be is not None:
            b = self.be
            out["be"] = {
                "parameter": b.parameter,
                "n": b.n,
                "gmr": b.gmr,
                "gmr_lower_90ci": b.gmr_lower_90ci,
                "gmr_upper_90ci": b.gmr_upper_90ci,
                "be_lower": b.be_lower,
                "be_upper": b.be_upper,
                "bioequivalent": b.bioequivalent,
                "cv_intra_pct": b.cv_intra_pct,
            }

        return out

    def report(self, path: str | Path) -> Path:
        """Write a multi-section pipeline report (HTML or Markdown by extension).

        Parameters
        ----------
        path : str or Path
            Output path. Extension ``.md`` / ``.markdown`` selects Markdown;
            otherwise HTML is used.

        Returns
        -------
        Path
            Resolved output path written.
        """
        from openpkflow.pipeline.reporting import report_pipeline

        return report_pipeline(self, path)

    def audit_bundle(self, path: str | Path) -> Path:
        """Write a reproducibility ZIP with inputs, results, report, and checksums.

        Parameters
        ----------
        path : str or Path
            Destination ZIP path.

        Returns
        -------
        Path
            Resolved archive path written.
        """
        from openpkflow.pipeline.reporting import write_audit_bundle

        return write_audit_bundle(self, path)


class StudyPipeline:
    """Run configured dissolution, NCA, and/or BE stages in sequence.

    Parameters
    ----------
    config : PipelineConfig
        Pipeline configuration. Must enable at least one stage.
    """

    def __init__(self, config: PipelineConfig) -> None:
        config.validate()
        self._config = config

    @property
    def config(self) -> PipelineConfig:
        """Return the pipeline configuration."""
        return self._config

    def run(self) -> StudyPipelineResult:
        """Execute all enabled stages and return an aggregated result.

        Returns
        -------
        StudyPipelineResult
            Stage results plus audit metadata.

        Raises
        ------
        FileNotFoundError
            If a configured CSV path does not exist.
        ValueError
            If a stage fails validation or analysis.
        """
        cfg = self._config
        generated_at = datetime.now(timezone.utc).isoformat()
        stages_requested = cfg.enabled_stages()
        stages_completed: list[str] = []
        stage_status: dict[str, str] = {s: "pending" for s in stages_requested}
        warnings: list[str] = []

        dissolution: ComparisonResult | None = None
        nca: NCASummaryResults | None = None
        be: BEResult | None = None

        metadata: dict[str, Any] = {
            "title": cfg.title,
            "openpkflow_version": __version__,
            "generated_at_utc": generated_at,
            "config": cfg.to_dict(),
            "stages_requested": list(stages_requested),
            "stages_completed": stages_completed,
            "stage_status": stage_status,
            "warnings": warnings,
            "methods": {
                "nca_auc_method": cfg.nca_auc_method if cfg.nca_csv is not None else None,
                "nca_blq_method": cfg.nca_blq_method if cfg.nca_csv is not None else None,
                "be_parameter": cfg.be_parameter if cfg.be_csv is not None else None,
                "be_limits": ([cfg.be_lower, cfg.be_upper] if cfg.be_csv is not None else None),
            },
            "disclaimer": _DISCLAIMER,
        }

        if "dissolution" in stages_requested:
            stage_status["dissolution"] = "running"
            try:
                dissolution = self._run_dissolution(cfg, warnings)
                stage_status["dissolution"] = "completed"
                stages_completed.append("dissolution")
            except Exception as exc:
                stage_status["dissolution"] = f"failed: {exc}"
                raise

        if "nca" in stages_requested:
            stage_status["nca"] = "running"
            try:
                nca = self._run_nca(cfg, warnings)
                stage_status["nca"] = "completed"
                stages_completed.append("nca")
            except Exception as exc:
                stage_status["nca"] = f"failed: {exc}"
                raise

        if "be" in stages_requested:
            stage_status["be"] = "running"
            try:
                be = self._run_be(cfg, warnings)
                stage_status["be"] = "completed"
                stages_completed.append("be")
            except Exception as exc:
                stage_status["be"] = f"failed: {exc}"
                raise

        return StudyPipelineResult(
            dissolution=dissolution,
            nca=nca,
            be=be,
            metadata=metadata,
        )

    @staticmethod
    def _run_dissolution(
        cfg: PipelineConfig,
        warnings: list[str],
    ) -> ComparisonResult:
        from openpkflow.dissolution.study import DissolutionStudy

        assert cfg.dissolution_csv is not None
        assert cfg.dissolution_reference is not None
        assert cfg.dissolution_test is not None

        path = Path(cfg.dissolution_csv)
        if not path.is_file():
            raise FileNotFoundError(f"dissolution_csv not found: {path}")

        study = DissolutionStudy.from_csv(path)
        result = study.compare(cfg.dissolution_reference, cfg.dissolution_test)
        if result.f2_value < 50.0:
            warnings.append(
                f"Dissolution f2={result.f2_value:.2f} < 50 "
                f"({result.reference_label} vs {result.test_label})."
            )
        return result

    @staticmethod
    def _run_nca(
        cfg: PipelineConfig,
        warnings: list[str],
    ) -> NCASummaryResults:
        from openpkflow.nca.study import NCAStudy

        assert cfg.nca_csv is not None
        path = Path(cfg.nca_csv)
        if not path.is_file():
            raise FileNotFoundError(f"nca_csv not found: {path}")

        auc_method = cfg.nca_auc_method
        if auc_method not in ("linear", "log", "linear_up_log_down"):
            raise ValueError(
                f"nca_auc_method must be 'linear', 'log', or 'linear_up_log_down' "
                f"(got {auc_method!r})."
            )
        typed_auc: Literal["linear", "log", "linear_up_log_down"] = auc_method  # type: ignore[assignment]

        if cfg.nca_blq_method is None:
            raise ValueError("nca_blq_method is required when nca_csv is set.")
        study = NCAStudy.from_csv(
            path,
            auc_method=typed_auc,
            blq_method=cfg.nca_blq_method,
        )
        summary = study.analyze()
        for r in summary.results:
            for w in r.warnings:
                warnings.append(f"NCA subject {r.subject}: {w}")
        return summary

    @staticmethod
    def _run_be(
        cfg: PipelineConfig,
        warnings: list[str],
    ) -> BEResult:
        import pandas as pd

        from openpkflow.be.study import BEStudy

        assert cfg.be_csv is not None
        path = Path(cfg.be_csv)
        if not path.is_file():
            raise FileNotFoundError(f"be_csv not found: {path}")

        df = pd.read_csv(path)
        seq_col = cfg.be_sequence_col
        if seq_col is not None and seq_col not in df.columns:
            seq_col = None
            warnings.append(
                f"BE sequence column {cfg.be_sequence_col!r} not found; running without sequence."
            )

        study = BEStudy(
            df,
            parameter=cfg.be_parameter,
            reference_col=cfg.be_reference_col,
            test_col=cfg.be_test_col,
            subject_col=cfg.be_subject_col,
            sequence_col=seq_col,
        )
        result = study.analyze(be_lower=cfg.be_lower, be_upper=cfg.be_upper)
        if not result.bioequivalent:
            warnings.append(
                f"BE parameter {result.parameter}: 90% CI "
                f"[{result.gmr_lower_90ci:.4f}, {result.gmr_upper_90ci:.4f}] "
                f"outside [{result.be_lower:.2f}, {result.be_upper:.2f}]."
            )
        return result
