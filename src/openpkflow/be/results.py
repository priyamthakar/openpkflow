"""BEResult dataclass and its summary/report methods."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    pass


@dataclass
class BEResult:
    """Output of :meth:`BEStudy.analyze`.

    Parameters
    ----------
    parameter : str
        PK parameter analysed (e.g. ``"AUCinf"``, ``"Cmax"``).
    n : int
        Number of matched subject pairs.
    gmr : float
        Geometric mean ratio test/reference.
    gmr_lower_90ci : float
        Lower bound of the 90% confidence interval for GMR.
    gmr_upper_90ci : float
        Upper bound of the 90% confidence interval for GMR.
    be_lower : float
        Lower acceptance limit (default 0.80).
    be_upper : float
        Upper acceptance limit (default 1.25).
    bioequivalent : bool
        True when the 90% CI lies entirely within [be_lower, be_upper].
    cv_intra_pct : float
        Intra-subject coefficient of variation (%).
    subjects_df : pd.DataFrame
        Per-subject data: subject, sequence (if known), reference, test, ratio,
        log_diff columns.
    """

    parameter: str
    n: int
    gmr: float
    gmr_lower_90ci: float
    gmr_upper_90ci: float
    be_lower: float
    be_upper: float
    bioequivalent: bool
    cv_intra_pct: float
    subjects_df: pd.DataFrame

    def summary(self) -> str:
        """Return an ASCII summary of the bioequivalence result.

        Returns
        -------
        str
            Multi-line ASCII summary table.
        """
        verdict = "BIOEQUIVALENT" if self.bioequivalent else "NOT BIOEQUIVALENT"
        lines = [
            "Bioequivalence Summary",
            "=" * 40,
            f"Parameter     : {self.parameter}",
            f"Subjects (n)  : {self.n}",
            f"GMR (T/R)     : {self.gmr:.4f}",
            f"90% CI        : [{self.gmr_lower_90ci:.4f}, {self.gmr_upper_90ci:.4f}]",
            f"Limits        : [{self.be_lower:.4f}, {self.be_upper:.4f}]",
            f"CV (intra)    : {self.cv_intra_pct:.1f}%",
            f"Conclusion    : {verdict}",
        ]
        return "\n".join(lines)

    def report(self, path: str | Path, format: str | None = None) -> None:
        """Write a bioequivalence report to *path*.

        Parameters
        ----------
        path : str | Path
            Output file path.  Format inferred from extension when *format* is None.
        format : {"html", "markdown", "md"}, optional
            Explicit format override.  Only HTML and Markdown are supported.

        Raises
        ------
        ValueError
            If an unsupported format is requested.
        """
        from openpkflow.be.reporting import report_be

        report_be(self, path, format=format)
