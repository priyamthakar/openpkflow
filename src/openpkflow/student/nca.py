"""Student-friendly NCA analysis: one function, all PK parameters.

Provides ``analyze_pk()`` which accepts a CSV path or arrays and returns
an ``NCAAnalysis`` object with per-subject PK parameters and plots.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from openpkflow.nca.results import NCASummaryResults


@dataclass
class SubjectProfile:
    """Single subject concentration-time profile.

    Parameters
    ----------
    subject_id : str
        Subject identifier.
    times : list[float]
        Sample times.
    concs : list[float]
        Observed concentrations.
    dose : float
        Administered dose.
    route : str
        Route of administration.
    """

    subject_id: str
    times: list[float]
    concs: list[float]
    dose: float
    route: str


@dataclass
class NCAAnalysis:
    """Result of a student-friendly NCA analysis.

    Attributes
    ----------
    subjects : dict[str, SubjectProfile]
        Loaded profiles keyed by subject ID.
    summary_results : NCASummaryResults or None
        Full NCA results from the engine.
    warnings : list[str]
        Any warnings encountered during analysis.
    """

    subjects: dict[str, SubjectProfile] = field(default_factory=dict)
    summary_results: NCASummaryResults | None = None
    warnings: list[str] = field(default_factory=list)

    def summary(self) -> str:
        """Print a human-readable summary of NCA results.

        Returns
        -------
        str
            Multi-line summary with per-subject and group statistics.
        """
        if self.summary_results is None:
            return "No NCA results available. Check input data."

        df = self.summary_results.to_dataframe()
        lines: list[str] = []
        lines.append("=" * 70)
        lines.append("  NON-COMPARTMENTAL ANALYSIS (NCA) SUMMARY")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"Subjects: {len(df)}")
        lines.append(f"AUC method: {self.summary_results.auc_method}")
        lines.append("")

        # Key parameters table
        params = [
            ("AUClast", "AUClast"),
            ("AUCinf", "AUCinf_obs"),
            ("Cmax", "Cmax"),
            ("Tmax", "Tmax"),
            ("t1/2", "half_life"),
            ("CL/F", "CL_F"),
            ("Vz/F", "Vz_F"),
        ]

        lines.append(f"{'Parameter':<12} {'Mean':>10} {'SD':>10} {'Min':>10} {'Max':>10}")
        lines.append("-" * 52)

        for display_name, col_name in params:
            if col_name in df.columns:
                vals = pd.to_numeric(df[col_name], errors="coerce").dropna()
                if len(vals) > 0:
                    mean_v = vals.mean()
                    std_v = vals.std() if len(vals) > 1 else 0.0
                    lines.append(
                        f"{display_name:<12} {mean_v:>10.3f} {std_v:>10.3f} "
                        f"{vals.min():>10.3f} {vals.max():>10.3f}"
                    )

        # Per-subject detail
        lines.append("")
        lines.append("-" * 70)
        lines.append("  PER-SUBJECT DETAIL")
        lines.append("-" * 70)

        for result in self.summary_results.results:
            lines.append(f"\nSubject: {result.subject}")
            lines.append(f"  Route: {result.route}  |  Dose: {result.dose}")
            lines.append(f"  AUClast: {result.AUClast:.3f}")
            if result.AUCinf_obs is not None:
                lines.append(f"  AUCinf:  {result.AUCinf_obs:.3f}")
            lines.append(f"  Cmax: {result.Cmax:.3f}  |  Tmax: {result.Tmax:.1f}")
            if result.half_life is not None:
                lines.append(f"  t1/2: {result.half_life:.2f}")
            if result.CL_F is not None:
                lines.append(f"  CL/F: {result.CL_F:.3f}  |  Vz/F: {result.Vz_F:.3f}")
            elif result.CL is not None:
                lines.append(f"  CL: {result.CL:.3f}  |  Vz: {result.Vz:.3f}")
            if result.warnings:
                for w in result.warnings:
                    lines.append(f"  WARNING: {w}")

        if self.warnings:
            lines.append("")
            lines.append("-" * 70)
            lines.append("  ANALYSIS WARNINGS")
            lines.append("-" * 70)
            for w in self.warnings:
                lines.append(f"  {w}")

        lines.append("")
        lines.append(
            "This report was generated using OpenPKFlow (open-source). "
            "Final regulatory interpretation should be reviewed by qualified "
            "formulation, pharmacokinetic, and regulatory experts."
        )
        return "\n".join(lines)

    def plot(self, output_path: str | Path | None = None, show: bool = False) -> None:
        """Plot concentration-time profiles for all subjects.

        Parameters
        ----------
        output_path : str or Path or None, optional
            Save figure to this path.
        show : bool, optional
            If True, display interactively (Jupyter). Default False.
        """
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        n_subjects = len(self.subjects)
        if n_subjects == 0:
            return

        # Layout: up to 4 per row
        cols = min(n_subjects, 4)
        rows = (n_subjects + cols - 1) // cols
        fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4 * rows), dpi=150)
        if n_subjects == 1:
            axes = np.array([axes])
        axes = np.atleast_2d(axes)

        colors = plt.cm.tab10(np.linspace(0, 1, min(n_subjects, 10)))

        for idx, (subj_id, prof) in enumerate(self.subjects.items()):
            row, col = divmod(idx, cols)
            ax = axes[row, col]

            t = np.array(prof.times)
            c = np.array(prof.concs)
            color = colors[idx % len(colors)]

            ax.plot(t, c, "o-", color=color, markersize=5, linewidth=1.5)
            ax.set_xlabel("Time (h)")
            ax.set_ylabel("Concentration")
            ax.set_title(f"Subject {subj_id}", fontweight="bold", fontsize=10)
            ax.grid(True, alpha=0.3)

            # Mark Cmax
            cmax_val = np.max(c)
            tmax_val = t[np.argmax(c)]
            ax.annotate(
                f"Cmax={cmax_val:.1f}",
                xy=(tmax_val, cmax_val),
                xytext=(10, 10),
                textcoords="offset points",
                fontsize=8,
                color=color,
                arrowprops=dict(arrowstyle="->", color=color, lw=0.8),
            )

        # Hide unused axes
        for idx in range(n_subjects, rows * cols):
            row, col = divmod(idx, cols)
            axes[row, col].set_visible(False)

        fig.suptitle("Concentration-Time Profiles", fontsize=13, fontweight="bold")
        fig.tight_layout()

        if output_path is not None:
            fig.savefig(output_path, bbox_inches="tight")
        if show:
            plt.show()
        plt.close(fig)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert NCA results to a pandas DataFrame.

        Returns
        -------
        pd.DataFrame
            One row per subject with all NCA parameters.
        """
        if self.summary_results is None:
            return pd.DataFrame()
        return self.summary_results.to_dataframe()


def _load_nca_data(
    source: str | Path | pd.DataFrame,
) -> pd.DataFrame:
    """Load NCA data from CSV path or DataFrame.

    Parameters
    ----------
    source : str, Path, or pd.DataFrame
        CSV file path or pre-loaded DataFrame.

    Returns
    -------
    pd.DataFrame
        Validated DataFrame with standard column names.
    """
    if isinstance(source, pd.DataFrame):
        df = source.copy()
    else:
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        df = pd.read_csv(path)

    # Auto-detect column names
    col_map: dict[str, str] = {}
    df_cols_lower = {c.lower().strip(): c for c in df.columns}

    required = {
        "subject": ["subject", "subj", "id", "subject_id", "usubjid"],
        "time": ["time", "t", "time_hr", "time_h", "hours", "hour"],
        "conc": ["conc", "concentration", "dv", "cp", "plasma"],
    }
    optional = {
        "dose": ["dose", "amt", "amount"],
        "route": ["route", "route_of_administration"],
    }

    for target, aliases in required.items():
        found = False
        for alias in aliases:
            if alias in df_cols_lower:
                col_map[target] = df_cols_lower[alias]
                found = True
                break
        if not found:
            raise ValueError(
                f"Could not find a '{target}' column. "
                f"Expected one of: {aliases}. "
                f"Available columns: {list(df.columns)}"
            )

    for target, aliases in optional.items():
        for alias in aliases:
            if alias in df_cols_lower:
                col_map[target] = df_cols_lower[alias]
                break

    df = df.rename(columns={v: k for k, v in col_map.items()})

    # Ensure numeric
    df["time"] = pd.to_numeric(df["time"], errors="coerce")
    df["conc"] = pd.to_numeric(df["conc"], errors="coerce")

    # Default dose and route if not present
    if "dose" not in df.columns:
        df["dose"] = 1.0
    else:
        df["dose"] = pd.to_numeric(df["dose"], errors="coerce").fillna(1.0)

    if "route" not in df.columns:
        df["route"] = "oral"

    # Drop rows with NaN in critical columns
    n_before = len(df)
    df = df.dropna(subset=["subject", "time", "conc"])
    if len(df) < n_before:
        import warnings

        warnings.warn(
            f"Dropped {n_before - len(df)} rows with missing data.",
            UserWarning,
            stacklevel=3,
        )

    return df


def analyze_pk(
    source: str | Path | pd.DataFrame,
    *,
    auc_method: str = "linear_up_log_down",
    subject_col: str = "subject",
    time_col: str = "time",
    conc_col: str = "conc",
    dose_col: str = "dose",
    route_col: str = "route",
) -> NCAAnalysis:
    """Run non-compartmental analysis on your PK data. One function, full NCA.

    Loads a CSV (or accepts a DataFrame), runs NCA per subject, and returns
    an NCAAnalysis object with all PK parameters, summary statistics, and plots.

    Parameters
    ----------
    source : str, Path, or pd.DataFrame
        CSV file path or pre-loaded DataFrame. Expected columns (case-insensitive):
        subject/id, time/t, conc/concentration, dose (optional), route (optional).
    auc_method : str, optional
        AUC calculation method: "linear", "log", or "linear_up_log_down".
        Default: "linear_up_log_down" (FDA recommended).
    subject_col : str, optional
        Column name for subject identifiers. Default "subject".
    time_col : str, optional
        Column name for sample times. Default "time".
    conc_col : str, optional
        Column name for concentrations. Default "conc".
    dose_col : str, optional
        Column name for dose. Default "dose".
    route_col : str, optional
        Column name for route. Default "route".

    Returns
    -------
    NCAAnalysis
        Results object with .summary(), .plot(), .to_dataframe() methods.

    Examples
    --------
    >>> results = analyze_pk("pk_data.csv")
    >>> print(results.summary())
    >>> results.plot("profiles.png")
    >>> df = results.to_dataframe()
    """
    from typing import Literal, cast

    df = _load_nca_data(source)

    # Extract subject profiles
    profiles: dict[str, SubjectProfile] = {}
    for subj, group in df.groupby(subject_col, sort=True):
        group_sorted = group.sort_values(time_col)
        subj_str = str(subj)
        profiles[subj_str] = SubjectProfile(
            subject_id=subj_str,
            times=group_sorted[time_col].tolist(),
            concs=group_sorted[conc_col].tolist(),
            dose=float(group_sorted[dose_col].dropna().iloc[0]),
            route=str(group_sorted[route_col].iloc[0]),
        )

    # Run NCA using the existing engine
    from openpkflow.nca.study import NCAStudy

    analysis_warnings: list[str] = []

    try:
        study = NCAStudy(
            df,
            auc_method=cast(Literal["linear", "log", "linear_up_log_down"], auc_method),
            blq_method="none",
            subject_col=subject_col,
            time_col=time_col,
            conc_col=conc_col,
            dose_col=dose_col,
            route_col=route_col,
        )
        summary_results = study.analyze()
    except Exception as exc:
        analysis_warnings.append(f"NCA analysis failed: {exc}")
        summary_results = None

    return NCAAnalysis(
        subjects=profiles,
        summary_results=summary_results,
        warnings=analysis_warnings,
    )
