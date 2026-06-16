"""Student-friendly dissolution analysis: fit all release models and compare profiles.

Provides ``fit_dissolution()`` which accepts a CSV path or DataFrame and returns
a ``DissolutionAnalysis`` object with ranked model fits, f1/f2 comparison, and plots.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from openpkflow.dissolution.models import (
    DissolutionFitResults,
    fit_dissolution_models,
)
from openpkflow.dissolution.similarity import f1, f2


@dataclass
class FormulationProfile:
    """Single formulation dissolution profile.

    Parameters
    ----------
    label : str
        Formulation name.
    time_points : list[float]
        Observed time points (minutes).
    mean_released : list[float]
        Mean percent dissolved at each time point.
    n_replicates : int
        Number of replicates (vessels/batches) per time point.
    cv_pct : list[float]
        Coefficient of variation (%) at each time point.
    """

    label: str
    time_points: list[float]
    mean_released: list[float]
    n_replicates: int
    cv_pct: list[float]


@dataclass
class DissolutionAnalysis:
    """Result of a student-friendly dissolution analysis.

    Attributes
    ----------
    formulations : dict[str, FormulationProfile]
        Loaded profiles keyed by label.
    fits : dict[str, DissolutionFitResults]
        Model fit results keyed by formulation label.
    comparison : ComparisonResult or None
        f1/f2 comparison if exactly two formulations were loaded.
    """

    formulations: dict[str, FormulationProfile] = field(default_factory=dict)
    fits: dict[str, DissolutionFitResults] = field(default_factory=dict)
    comparison: object | None = None

    def summary(self) -> str:
        """Print a human-readable summary of all results.

        Returns
        -------
        str
            Multi-line summary text.
        """
        lines: list[str] = []
        lines.append("=" * 60)
        lines.append("  DISSOLUTION ANALYSIS SUMMARY")
        lines.append("=" * 60)
        lines.append("")

        # Profile summaries
        for label, prof in self.formulations.items():
            lines.append(f"Formulation: {label}")
            lines.append(f"  Time points: {len(prof.time_points)}")
            lines.append(f"  Replicates per timepoint: {prof.n_replicates}")
            if prof.cv_pct:
                max_cv = max(prof.cv_pct)
                lines.append(f"  Max CV%: {max_cv:.1f}%")
            lines.append(f"  Final dissolution: {prof.mean_released[-1]:.1f}%")
            lines.append("")

        # Model fitting results
        for _label, fit_result in self.fits.items():
            lines.append(fit_result.summary())
            lines.append("")

        # Comparison
        if self.comparison is not None:
            comp = self.comparison
            lines.append("-" * 60)
            lines.append("  SIMILARITY COMPARISON")
            lines.append("-" * 60)
            lines.append(f"  Reference: {comp.reference_label}")
            lines.append(f"  Test:      {comp.test_label}")
            lines.append(f"  f1 (difference): {comp.f1_value:.2f}")
            lines.append(f"  f2 (similarity): {comp.f2_value:.2f}")
            if comp.f2_value >= 50.0:
                lines.append("  Verdict: SIMILAR (f2 >= 50)")
            else:
                lines.append("  Verdict: NOT SIMILAR (f2 < 50)")
            lines.append("")

        lines.append(
            "This report was generated using OpenPKFlow (open-source). "
            "Final regulatory interpretation should be reviewed by qualified "
            "formulation, pharmacokinetic, and regulatory experts."
        )
        return "\n".join(lines)

    def plot(self, output_path: str | Path | None = None, show: bool = False) -> None:
        """Plot dissolution profiles with fitted model overlays.

        Parameters
        ----------
        output_path : str or Path or None, optional
            Save figure to this path. If None and show=False, does nothing.
        show : bool, optional
            If True, display interactively (Jupyter). Default False.
        """
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        n_forms = len(self.formulations)

        fig, axes = plt.subplots(1, max(n_forms, 1), figsize=(6 * max(n_forms, 1), 5), dpi=150)
        if n_forms == 1:
            axes = [axes]

        colors = ["#e63946", "#457b9d", "#2a9d8f", "#e9c46a", "#f4a261", "#264653"]

        for idx, (label, prof) in enumerate(self.formulations.items()):
            ax = axes[idx]
            t = np.array(prof.time_points)
            q = np.array(prof.mean_released)

            ax.scatter(t, q, color="#003366", s=50, zorder=5, label="Observed")

            if label in self.fits:
                fit_result = self.fits[label]
                converged = sorted(
                    [f for f in fit_result.fits if f.converged], key=lambda m: m.aicc
                )
                t_dense = np.linspace(0, float(t.max()), 200)
                for i, fit in enumerate(converged[:3]):  # top 3 models only
                    q_fit = fit.predict(t_dense)
                    ax.plot(
                        t_dense,
                        q_fit,
                        color=colors[i % len(colors)],
                        linewidth=1.5,
                        label=f"{fit.model_name} (AICc={fit.aicc:.1f})",
                    )

            ax.set_xlabel("Time (min)")
            ax.set_ylabel("% Dissolved")
            ax.set_title(label, fontweight="bold")
            ax.set_ylim(0, 110)
            ax.legend(fontsize=8, loc="lower right")
            ax.grid(True, alpha=0.3)

        # Add comparison subplot if available
        if self.comparison is not None:
            comp = self.comparison
            # We need an extra axis - recreate figure
            plt.close(fig)
            fig, axes = plt.subplots(1, n_forms + 1, figsize=(6 * (n_forms + 1), 5), dpi=150)
            if n_forms == 0:
                axes = [axes]

            # Re-plot formulations
            for idx, (label, prof) in enumerate(self.formulations.items()):
                ax = axes[idx]
                t = np.array(prof.time_points)
                q = np.array(prof.mean_released)
                ax.scatter(t, q, color="#003366", s=50, zorder=5, label="Observed")
                if label in self.fits:
                    fit_result = self.fits[label]
                    converged = sorted(
                        [f for f in fit_result.fits if f.converged],
                        key=lambda m: m.aicc,
                    )
                    t_dense = np.linspace(0, float(t.max()), 200)
                    for i, fit in enumerate(converged[:3]):
                        q_fit = fit.predict(t_dense)
                        ax.plot(
                            t_dense,
                            q_fit,
                            color=colors[i % len(colors)],
                            linewidth=1.5,
                            label=f"{fit.model_name} (AICc={fit.aicc:.1f})",
                        )
                ax.set_xlabel("Time (min)")
                ax.set_ylabel("% Dissolved")
                ax.set_title(label, fontweight="bold")
                ax.set_ylim(0, 110)
                ax.legend(fontsize=8, loc="lower right")
                ax.grid(True, alpha=0.3)

            # Comparison plot
            ax_comp = axes[-1]
            tp = np.array(comp.time_points)
            ax_comp.plot(
                tp,
                comp.reference_mean,
                "o-",
                color="#003366",
                linewidth=2,
                markersize=6,
                label=comp.reference_label,
            )
            ax_comp.plot(
                tp,
                comp.test_mean,
                "s--",
                color="#cc3300",
                linewidth=2,
                markersize=6,
                label=comp.test_label,
            )
            ax_comp.axhline(85, color="#888", linestyle=":", linewidth=1, label="85%")
            verdict = "SIMILAR" if comp.f2_value >= 50 else "NOT SIMILAR"
            ax_comp.set_title(
                f"f1={comp.f1_value:.1f}  f2={comp.f2_value:.1f}  [{verdict}]",
                fontweight="bold",
            )
            ax_comp.set_xlabel("Time (min)")
            ax_comp.set_ylabel("% Dissolved")
            ax_comp.set_ylim(0, 110)
            ax_comp.legend(fontsize=8)
            ax_comp.grid(True, alpha=0.3)

        fig.tight_layout()
        if output_path is not None:
            fig.savefig(output_path, bbox_inches="tight")
        if show:
            plt.show()
        plt.close(fig)


def _load_dissolution_data(
    source: str | Path | pd.DataFrame,
) -> pd.DataFrame:
    """Load dissolution data from CSV path or DataFrame.

    Parameters
    ----------
    source : str, Path, or pd.DataFrame
        CSV file path or pre-loaded DataFrame.

    Returns
    -------
    pd.DataFrame
        Validated DataFrame with required columns.

    Raises
    ------
    FileNotFoundError
        If CSV file does not exist.
    ValueError
        If required columns are missing.
    """
    if isinstance(source, pd.DataFrame):
        df = source.copy()
    else:
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        df = pd.read_csv(path)

    # Auto-detect column names (case-insensitive)
    col_map: dict[str, str] = {}
    df_cols_lower = {c.lower().strip(): c for c in df.columns}

    for target, aliases in [
        ("formulation", ["formulation", "form", "product", "batch_label"]),
        ("time", ["time", "t", "time_min", "time_hr", "minutes", "hours"]),
        (
            "percent_released",
            [
                "percent_released",
                "pct_released",
                "dissolved",
                "%dissolved",
                "%released",
                "percent",
                "pct",
            ],
        ),
    ]:
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

    # Rename to standard names
    df = df.rename(columns={v: k for k, v in col_map.items()})

    # Ensure numeric
    df["time"] = pd.to_numeric(df["time"], errors="coerce")
    df["percent_released"] = pd.to_numeric(df["percent_released"], errors="coerce")

    # Drop rows with NaN in critical columns
    n_before = len(df)
    df = df.dropna(subset=["formulation", "time", "percent_released"])
    if len(df) < n_before:
        import warnings

        warnings.warn(
            f"Dropped {n_before - len(df)} rows with missing data.",
            UserWarning,
            stacklevel=3,
        )

    return df


def _extract_profiles(df: pd.DataFrame) -> dict[str, FormulationProfile]:
    """Extract per-formulation mean profiles from a dissolution DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with formulation, time, percent_released columns.

    Returns
    -------
    dict[str, FormulationProfile]
        Profiles keyed by formulation label.
    """
    profiles: dict[str, FormulationProfile] = {}

    for label, group in df.groupby("formulation"):
        label_str = str(label)
        stats = group.groupby("time")["percent_released"].agg(["mean", "std", "count"])
        stats = stats.reset_index().sort_values("time")

        time_points = stats["time"].tolist()
        mean_released = stats["mean"].tolist()
        n_reps = int(stats["count"].max())

        cv_pct = []
        for _, row in stats.iterrows():
            m = row["mean"]
            s = row["std"]
            if pd.isna(s) or m == 0:
                cv_pct.append(0.0)
            else:
                cv_pct.append(float(s / m * 100.0))

        profiles[label_str] = FormulationProfile(
            label=label_str,
            time_points=time_points,
            mean_released=mean_released,
            n_replicates=n_reps,
            cv_pct=cv_pct,
        )

    return profiles


def fit_dissolution(
    source: str | Path | pd.DataFrame,
    *,
    models: list[str] | None = None,
    reference: str | None = None,
    test: str | None = None,
) -> DissolutionAnalysis:
    """Fit dissolution release models to your data. One function, full analysis.

    Loads a CSV (or accepts a DataFrame), extracts per-formulation mean profiles,
    fits standard release kinetics models, ranks them by AICc, and optionally
    computes f1/f2 similarity between two formulations.

    Parameters
    ----------
    source : str, Path, or pd.DataFrame
        CSV file path or pre-loaded DataFrame. Expected columns (case-insensitive):
        formulation/product, time/t, percent_released/dissolved.
    models : list[str] or None, optional
        Models to fit. Default: all six (zero_order, first_order, higuchi,
        korsmeyer_peppas, weibull, hixson_crowell).
    reference : str or None, optional
        Label of the reference formulation for f1/f2 comparison.
        Auto-detected if exactly two formulations exist.
    test : str or None, optional
        Label of the test formulation for f1/f2 comparison.

    Returns
    -------
    DissolutionAnalysis
        Results object with .summary(), .plot(), .fits, .comparison attributes.

    Raises
    ------
    FileNotFoundError
        If CSV file does not exist.
    ValueError
        If required columns are missing or data is invalid.

    Examples
    --------
    >>> results = fit_dissolution("dissolution_data.csv")
    >>> print(results.summary())
    >>> results.plot("output.png")

    >>> # With explicit comparison
    >>> results = fit_dissolution("data.csv", reference="Innovator", test="Generic")
    """
    df = _load_dissolution_data(source)
    profiles = _extract_profiles(df)

    # Fit models for each formulation
    all_models = models or [
        "zero_order",
        "first_order",
        "higuchi",
        "korsmeyer_peppas",
        "weibull",
        "hixson_crowell",
    ]

    fits: dict[str, DissolutionFitResults] = {}
    for label, prof in profiles.items():
        try:
            fit_result = fit_dissolution_models(
                time_points=prof.time_points,
                observed_mean=prof.mean_released,
                models=all_models,
                formulation_label=label,
            )
            fits[label] = fit_result
        except Exception as exc:
            import warnings

            warnings.warn(
                f"Model fitting failed for '{label}': {exc}",
                UserWarning,
                stacklevel=2,
            )

    # Auto-detect comparison if exactly two formulations
    comparison = None
    labels = list(profiles.keys())

    if reference is not None and test is not None:
        ref_label, test_label = reference, test
    elif len(labels) == 2:
        ref_label, test_label = labels[0], labels[1]
    else:
        ref_label = test_label = None

    if ref_label and test_label and ref_label in profiles and test_label in profiles:
        ref_prof = profiles[ref_label]
        test_prof = profiles[test_label]

        if ref_prof.time_points == test_prof.time_points:
            f1_val = f1(ref_prof.mean_released, test_prof.mean_released)
            f2_val = f2(ref_prof.mean_released, test_prof.mean_released)

            from dataclasses import dataclass as _dc

            @_dc
            class _CompResult:
                reference_label: str
                test_label: str
                f1_value: float
                f2_value: float
                n_timepoints: int
                reference_mean: list[float]
                test_mean: list[float]
                time_points: list[float]

            comparison = _CompResult(
                reference_label=ref_label,
                test_label=test_label,
                f1_value=f1_val,
                f2_value=f2_val,
                n_timepoints=len(ref_prof.time_points),
                reference_mean=ref_prof.mean_released,
                test_mean=test_prof.mean_released,
                time_points=ref_prof.time_points,
            )

    return DissolutionAnalysis(
        formulations=profiles,
        fits=fits,
        comparison=comparison,
    )
