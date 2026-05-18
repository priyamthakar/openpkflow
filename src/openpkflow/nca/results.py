"""NCA result dataclasses: NCAResult (per-subject) and NCASummaryResults (collection)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pandas as pd


@dataclass
class NCAResult:
    """Non-compartmental analysis result for a single subject.

    Parameters
    ----------
    subject : str
        Subject identifier.
    route : str
        Route of administration.
    dose : float
        Administered dose.
    auc_method : str
        AUC calculation method used.
    blq_method : str
        BLQ handling method used.
    AUClast : float
        AUC from time 0 to last quantifiable time point.
    AUCinf_obs : float or None
        AUC extrapolated to infinity using last observed concentration.
    AUC_percent_extrapolated : float or None
        Percentage of AUCinf that is extrapolated.
    Cmax : float
        Maximum observed concentration.
    Tmax : float
        Time of maximum observed concentration.
    lambda_z : float or None
        Terminal elimination rate constant.
    half_life : float or None
        Terminal half-life.
    lambda_z_method : str or None
        Method used for lambda_z estimation.
    selected_lambda_z_times : list[float]
        Time points used in the lambda_z regression.
    selected_lambda_z_concs : list[float]
        Concentrations used in the lambda_z regression.
    CL_F : float or None
        Apparent oral clearance (oral route only).
    Vz_F : float or None
        Apparent oral volume of distribution (oral route only).
    CL : float or None
        Absolute IV clearance (IV routes only).
    Vz : float or None
        Absolute IV volume of distribution (IV routes only).
    warnings : list[str]
        Warnings generated during analysis.
    """

    subject: str
    route: str
    dose: float
    auc_method: str
    blq_method: str

    # Primary PK parameters
    AUClast: float
    AUCinf_obs: float | None
    AUC_percent_extrapolated: float | None
    Cmax: float
    Tmax: float

    # Terminal phase
    lambda_z: float | None
    half_life: float | None
    lambda_z_method: str | None
    selected_lambda_z_times: list[float] = field(default_factory=list)
    selected_lambda_z_concs: list[float] = field(default_factory=list)

    # Clearance/Volume -- exactly one pair is populated depending on route
    CL_F: float | None = None   # oral apparent clearance
    Vz_F: float | None = None   # oral apparent volume
    CL: float | None = None     # IV absolute clearance
    Vz: float | None = None     # IV absolute volume

    warnings: list[str] = field(default_factory=list)

    def summary(self) -> str:
        """Return an ASCII-only plain text summary of the NCA result.

        Returns
        -------
        str
            Multi-line summary of all PK parameters.
        """
        def _fmt(v: float | None) -> str:
            return f"{v:.4g}" if v is not None else "N/A"

        lines = [
            "NCA Result Summary",
            "==================",
            f"Subject    : {self.subject}",
            f"Route      : {self.route}",
            f"Dose       : {self.dose}",
            f"AUC method : {self.auc_method}",
            f"BLQ method : {self.blq_method}",
            "",
            "PK Parameters",
            "-------------",
            f"Cmax                    : {_fmt(self.Cmax)}",
            f"Tmax                    : {_fmt(self.Tmax)}",
            f"AUClast                 : {_fmt(self.AUClast)}",
            f"AUCinf_obs              : {_fmt(self.AUCinf_obs)}",
            f"AUC_percent_extrapolated: {_fmt(self.AUC_percent_extrapolated)}",
            f"lambda_z                : {_fmt(self.lambda_z)}",
            f"half_life               : {_fmt(self.half_life)}",
            f"lambda_z_method         : {self.lambda_z_method or 'N/A'}",
            f"CL_F                    : {_fmt(self.CL_F)}",
            f"Vz_F                    : {_fmt(self.Vz_F)}",
            f"CL                      : {_fmt(self.CL)}",
            f"Vz                      : {_fmt(self.Vz)}",
        ]

        if self.warnings:
            lines.append("")
            lines.append("Warnings")
            lines.append("--------")
            for w in self.warnings:
                lines.append(f"  - {w}")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Return a flat dict of all fields.

        Returns
        -------
        dict[str, Any]
            All fields including Nones. List fields remain as lists.
        """
        return {
            "subject": self.subject,
            "route": self.route,
            "dose": self.dose,
            "auc_method": self.auc_method,
            "blq_method": self.blq_method,
            "AUClast": self.AUClast,
            "AUCinf_obs": self.AUCinf_obs,
            "AUC_percent_extrapolated": self.AUC_percent_extrapolated,
            "Cmax": self.Cmax,
            "Tmax": self.Tmax,
            "lambda_z": self.lambda_z,
            "half_life": self.half_life,
            "lambda_z_method": self.lambda_z_method,
            "selected_lambda_z_times": self.selected_lambda_z_times,
            "selected_lambda_z_concs": self.selected_lambda_z_concs,
            "CL_F": self.CL_F,
            "Vz_F": self.Vz_F,
            "CL": self.CL,
            "Vz": self.Vz,
            "warnings": self.warnings,
        }

    def report(
        self,
        output_path: str | Path,
        *,
        format: str = "html",
    ) -> str | bytes:
        """Generate a report for this NCA result.

        Parameters
        ----------
        output_path : str | Path
            Where to save the report file.
        format : str, optional
            Output format: ``"html"`` or ``"markdown"``. Defaults to ``"html"``.

        Returns
        -------
        str | bytes
            Rendered content (str for html/markdown).
        """
        from openpkflow.nca.reporting import report_nca_single

        return report_nca_single(self, output_path=output_path, format=format)


@dataclass
class NCASummaryResults:
    """Collection of NCA results from a multi-subject study.

    Parameters
    ----------
    results : list[NCAResult]
        Per-subject NCA results.
    study_label : str, optional
        Optional label for the study.
    auc_method : str, optional
        AUC method used across the study.
    blq_method : str, optional
        BLQ method used across the study.
    """

    results: list[NCAResult]
    study_label: str = ""
    auc_method: str = ""
    blq_method: str = ""

    def summary(self) -> str:
        """Return an ASCII-only tabular summary of all subjects.

        Returns
        -------
        str
            Fixed-width table with one row per subject.
        """
        def _fmt(v: float | None) -> str:
            return f"{v:.4g}" if v is not None else "N/A"

        def _cl(r: NCAResult) -> str:
            if r.CL_F is not None:
                return f"{r.CL_F:.4g}"
            if r.CL is not None:
                return f"{r.CL:.4g}"
            return "N/A"

        def _vz(r: NCAResult) -> str:
            if r.Vz_F is not None:
                return f"{r.Vz_F:.4g}"
            if r.Vz is not None:
                return f"{r.Vz:.4g}"
            return "N/A"

        header = (
            f"{'Subject':<12} {'AUClast':>10} {'AUCinf_obs':>12} {'Cmax':>10} "
            f"{'Tmax':>8} {'half_life':>10} {'CL/CL_F':>10} {'Vz/Vz_F':>10}"
        )
        sep = "-" * len(header)
        lines = [header, sep]

        for r in self.results:
            lines.append(
                f"{r.subject:<12} {_fmt(r.AUClast):>10} {_fmt(r.AUCinf_obs):>12} "
                f"{_fmt(r.Cmax):>10} {_fmt(r.Tmax):>8} {_fmt(r.half_life):>10} "
                f"{_cl(r):>10} {_vz(r):>10}"
            )

        if self.study_label:
            lines.insert(0, f"Study: {self.study_label}")
            lines.insert(1, "")

        return "\n".join(lines)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert all results to a pandas DataFrame.

        Returns
        -------
        pd.DataFrame
            One row per subject with all NCAResult fields as columns.
        """
        import pandas as pd

        rows = [r.to_dict() for r in self.results]
        return pd.DataFrame(rows)

    def report(
        self,
        output_path: str | Path,
        *,
        format: str = "html",
    ) -> str | bytes:
        """Generate a summary report for all subjects.

        Parameters
        ----------
        output_path : str | Path
            Where to save the report file.
        format : str, optional
            Output format: ``"html"`` or ``"markdown"``. Defaults to ``"html"``.

        Returns
        -------
        str | bytes
            Rendered content (str for html/markdown).
        """
        from openpkflow.nca.reporting import report_nca_summary

        return report_nca_summary(self, output_path=output_path, format=format)
