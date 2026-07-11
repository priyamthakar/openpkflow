"""High-level DissolutionStudy API."""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from .loader import (
    DissolutionCSVConfig,
    get_formulation_means,
    load_dissolution_csv,
    load_dissolution_excel,
)
from .similarity import f1, f2

if TYPE_CHECKING:
    from .bootstrap import BootstrapF2Result
    from .models import DissolutionFitResults

_85_PCT_WARNING = (
    "More than one mean dissolution value exceeds 85%% in the %s profile "
    "(%d timepoints above 85%%). Per common regulatory practice, only one "
    "timepoint above 85%% should be included in the f2 calculation. "
    "Review your timepoint selection."
)


@dataclass
class ComparisonResult:
    """Result of an f1/f2 dissolution similarity comparison.

    Parameters
    ----------
    reference_label : str
        Label of the reference formulation.
    test_label : str
        Label of the test formulation.
    f1_value : float
        Computed f1 difference factor.
    f2_value : float
        Computed f2 similarity factor.
    n_timepoints : int
        Number of matched time points used in the comparison.
    reference_mean : list[float]
        Mean percent released for the reference formulation at each time point.
    test_mean : list[float]
        Mean percent released for the test formulation at each time point.
    time_points : list[float]
        Shared time points used in the comparison.
    f2_method : str
        Explicit f2 time-point selection method (``"all_points"`` or
        ``"regulatory"``).
    warnings : list[str]
        Prerequisite / variability warnings captured during compare().
    """

    reference_label: str
    test_label: str
    f1_value: float
    f2_value: float
    n_timepoints: int
    reference_mean: list[float]
    test_mean: list[float]
    time_points: list[float] = field(default_factory=list)
    f2_method: str = "all_points"
    warnings: list[str] = field(default_factory=list)

    def summary(self) -> str:
        """Return a human-readable text summary of the comparison result.

        Returns
        -------
        str
            Multi-line summary including f1, f2, interpretation, and disclaimer.
        """
        method_note = (
            "regulatory (FDA 85% rule time-point trimming)"
            if self.f2_method == "regulatory"
            else "all_points (no 85% rule trimming; not the FDA default selection)"
        )
        if self.f2_method == "regulatory":
            interpretation = (
                "f2 >= 50 supports similarity under the regulatory time-point method."
                if self.f2_value >= 50.0
                else "f2 < 50 does not support similarity under the regulatory time-point method."
            )
        else:
            interpretation = (
                f"f2 = {self.f2_value:.2f} with method=all_points. "
                "Do not claim FDA-supporting similarity from all_points alone; "
                "re-run with f2_method='regulatory' for the FDA 85% rule selection."
            )
        lines = [
            "Dissolution Similarity Analysis",
            "================================",
            f"Reference: {self.reference_label}  |  Test: {self.test_label}",
            f"Timepoints used: {self.n_timepoints}  |  f2_method: {self.f2_method} ({method_note})",
            "",
            f"f1 (difference factor): {self.f1_value:.2f}",
            f"f2 (similarity factor): {self.f2_value:.2f}",
            "",
            f"Interpretation: {interpretation}",
        ]
        if self.warnings:
            lines.append("")
            lines.append("Warnings / prerequisites:")
            for w in self.warnings:
                lines.append(f"  - {w}")
        lines.extend(
            [
                "",
                "Disclaimer: This output was generated using OpenPKFlow (open-source).",
                "Final regulatory interpretation should be reviewed by qualified experts.",
            ]
        )
        return "\n".join(lines)

    def report(
        self,
        output_path: str | Path,
        format: str = "html",
    ) -> str | bytes:
        """Generate a report for this comparison result.

        Parameters
        ----------
        output_path : str | Path
            Where to save the report file.
        format : str, optional
            Output format: ``"html"``, ``"markdown"``, ``"pdf"``, or ``"docx"``.
            Defaults to ``"html"``.

        Returns
        -------
        str | bytes
            Rendered content (str for html/markdown, bytes for pdf/docx).
        """
        from .reporting import report_dissolution

        return report_dissolution(
            output_path=output_path,
            format=format,
            title=f"Dissolution Similarity: {self.reference_label} vs {self.test_label}",
            reference_label=self.reference_label,
            test_label=self.test_label,
            f1_value=self.f1_value,
            f2_value=self.f2_value,
            n_timepoints=self.n_timepoints,
            time_points=self.time_points,
            reference_mean=self.reference_mean,
            test_mean=self.test_mean,
        )

    def plot(
        self,
        output_path: str | Path | None = None,
        show: bool = False,
    ) -> None:
        """Plot the dissolution profiles for reference and test.

        Parameters
        ----------
        output_path : str or Path or None, optional
            If provided, saves the figure to this path (PNG/PDF/SVG).
        show : bool, optional
            If True, calls plt.show() to display interactively. Default False.
        """
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        tp = np.array(self.time_points)
        fig, ax = plt.subplots(figsize=(7, 4), dpi=600)
        ax.plot(
            tp,
            self.reference_mean,
            "o-",
            color="#003366",
            linewidth=2,
            markersize=6,
            label=self.reference_label,
        )
        ax.plot(
            tp,
            self.test_mean,
            "s--",
            color="#cc3300",
            linewidth=2,
            markersize=6,
            label=self.test_label,
        )
        ax.axhline(85, color="#888888", linestyle=":", linewidth=1, label="85% threshold")
        verdict = "SIMILAR" if self.f2_value >= 50.0 else "NOT SIMILAR"
        ax.set_title(
            f"Dissolution Profile  |  f1={self.f1_value:.1f}  f2={self.f2_value:.1f}  [{verdict}]",
            fontsize=11,
        )
        ax.set_xlabel("Time (min)", fontsize=10)
        ax.set_ylabel("Mean % Dissolved", fontsize=10)
        ax.set_ylim(0, 105)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
        fig.tight_layout()

        if output_path is not None:
            fig.savefig(output_path, bbox_inches="tight")
        if show:
            plt.show()
        plt.close(fig)

    def to_dict(self) -> dict[str, object]:
        """Return a plain-dict representation of the result.

        Returns
        -------
        dict[str, object]
            All fields serialized to basic Python types.
        """
        return {
            "reference_label": self.reference_label,
            "test_label": self.test_label,
            "f1_value": self.f1_value,
            "f2_value": self.f2_value,
            "n_timepoints": self.n_timepoints,
            "reference_mean": self.reference_mean,
            "test_mean": self.test_mean,
            "time_points": self.time_points,
        }


def _check_cv(
    df: pd.DataFrame,
    formulation: str,
    config: DissolutionCSVConfig,
) -> list[str]:
    """Return warning strings for timepoints where CV exceeds FDA limits."""
    col_form = config.formulation_col
    col_time = config.time_col
    col_pct = config.percent_released_col

    subset = df[df[col_form] == formulation]
    warnings_out: list[str] = []

    for time_val, group in subset.groupby(col_time):
        vals = group[col_pct].values
        if len(vals) < 2:
            continue
        mean_val = float(vals.mean())
        if mean_val == 0.0:
            continue
        cv = float(vals.std(ddof=1) / mean_val * 100.0)
        limit = 20.0 if float(time_val) <= 15.0 else 10.0
        if cv > limit:
            warnings_out.append(
                f"{formulation} at t={time_val}: CV={cv:.1f}% exceeds FDA limit of {limit:.0f}%"
            )

    return warnings_out


def _check_ich_m13b_sd(
    df: pd.DataFrame,
    formulation: str,
    config: DissolutionCSVConfig,
) -> list[str]:
    """Check ICH M13B Step 2 absolute SD criterion (SD <= 8% at all time points).

    ICH M13B Step 2 draft (2025) defines high variability as absolute SD > 8%
    at any time point (not relative SD restricted to mean <= 60%). When SD > 8%,
    point-estimate f2 alone is not sufficient; bootstrap f2 CI is indicated.

    Returns
    -------
    list[str]
        Warning strings for timepoints where absolute SD exceeds 8%.

    References
    ----------
    ICH M13B Draft Guideline Step 2 (2025-02-12): Bioequivalence for Immediate-
    Release Solid Oral Dosage Forms - Additional Strengths Biowaiver.
    """
    col_form = config.formulation_col
    col_time = config.time_col
    col_pct = config.percent_released_col

    subset = df[df[col_form] == formulation]
    warnings_out: list[str] = []

    for time_val, group in subset.groupby(col_time):
        vals = group[col_pct].values
        if len(vals) < 2:
            continue
        sd = float(vals.std(ddof=1))
        if sd > 8.0:
            warnings_out.append(
                f"{formulation} at t={time_val}: SD={sd:.1f}% exceeds "
                f"ICH M13B Step 2 limit of 8% absolute SD (mean {float(vals.mean()):.1f}%)"
            )

    return warnings_out


# Backward-compatible alias (deprecated name; uses Step 2 absolute SD logic)
_check_ich_m13b_rsd = _check_ich_m13b_sd


class DissolutionStudy:
    """High-level dissolution study object.

    Load dissolution data, run comparisons, fit models, and generate reports.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        config: DissolutionCSVConfig | None = None,
    ) -> None:
        """Initialise a DissolutionStudy from a validated DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            Dissolution data with columns: formulation, batch, time, percent_released.
        config : DissolutionCSVConfig | None, optional
            Column name configuration. Uses defaults if None.
        """
        self._df = df
        self._config = config or DissolutionCSVConfig()

    @classmethod
    def from_csv(
        cls,
        path: str | Path,
        config: DissolutionCSVConfig | None = None,
    ) -> DissolutionStudy:
        """Load a DissolutionStudy from a CSV file.

        Parameters
        ----------
        path : str | Path
            Path to a dissolution CSV file.
        config : DissolutionCSVConfig | None, optional
            Column name configuration. Uses defaults if None.

        Returns
        -------
        DissolutionStudy
            Loaded and validated study object.

        Raises
        ------
        FileNotFoundError
            If the CSV file does not exist.
        ValueError
            If the CSV data fails validation.
        """
        df = load_dissolution_csv(path, config)
        return cls(df)

    @classmethod
    def from_excel(
        cls,
        path: str | Path,
        config: DissolutionCSVConfig | None = None,
        sheet_name: str | int = 0,
    ) -> DissolutionStudy:
        """Load a DissolutionStudy from an Excel file (.xlsx or .xls).

        Requires ``openpyxl`` (included in ``pip install openpkflow[reports]``).

        Parameters
        ----------
        path : str | Path
            Path to an Excel file (.xlsx or .xls).
        config : DissolutionCSVConfig | None, optional
            Column name configuration. Uses defaults if None.
        sheet_name : str or int, optional
            Sheet name or zero-based index. Defaults to the first sheet (0).

        Returns
        -------
        DissolutionStudy
            Loaded and validated study object.

        Raises
        ------
        FileNotFoundError
            If the Excel file does not exist.
        ImportError
            If openpyxl is not installed (pip install openpkflow[reports]).
        ValueError
            If the data fails validation.
        """
        df = load_dissolution_excel(path, config, sheet_name=sheet_name)
        return cls(df)

    def formulations(self) -> list[str]:
        """List all formulation labels in the dataset.

        Returns
        -------
        list[str]
            Unique formulation labels in the order they appear.
        """
        return list(self._df["formulation"].unique())

    def compare(
        self,
        reference: str,
        test: str,
        *,
        f2_method: str = "regulatory",
    ) -> ComparisonResult:
        """Compare two formulations using f1 and f2.

        Profiles are averaged across batches per time point before computing
        f1 and f2.  Reference and test must share identical time points.

        Parameters
        ----------
        reference : str
            Label of the reference formulation.
        test : str
            Label of the test formulation.
        f2_method : {"regulatory", "all_points"}, optional
            Time-point selection for f2. Default ``"regulatory"`` applies the
            FDA 85% rule. ``"all_points"`` uses every supplied time point and
            must not be reported as FDA-supporting without stating the method.

        Returns
        -------
        ComparisonResult
            Computed f1, f2, method label, and persisted prerequisite warnings.

        Raises
        ------
        ValueError
            If either formulation label is not found in the dataset, if the
            reference and test profiles do not share the same time points,
            or if f2_method is unknown.
        """
        if f2_method not in ("regulatory", "all_points"):
            raise ValueError(f"f2_method must be 'regulatory' or 'all_points' (got {f2_method!r}).")

        available = self.formulations()

        if reference not in available:
            raise ValueError(
                f"Reference formulation '{reference}' not found. Available: {available}"
            )
        if test not in available:
            raise ValueError(f"Test formulation '{test}' not found. Available: {available}")

        ref_times, ref_means = get_formulation_means(self._df, reference)
        tst_times, tst_means = get_formulation_means(self._df, test)

        if ref_times != tst_times:
            raise ValueError(
                f"Reference and test formulations do not share the same time points.\n"
                f"  Reference time points: {ref_times}\n"
                f"  Test time points:      {tst_times}"
            )

        persisted: list[str] = []

        # Regulatory 85% check: warn if more than one timepoint exceeds 85%
        for label, means in ((reference, ref_means), (test, tst_means)):
            n_above_85 = sum(1 for v in means if v > 85.0)
            if n_above_85 > 1:
                msg = _85_PCT_WARNING % (label, n_above_85)
                persisted.append(msg)
                warnings.warn(msg, UserWarning, stacklevel=2)

        # CV check per FDA dissolution guidance (CV <= 20% early, <= 10% later)
        cv_issues: list[str] = []
        cv_issues.extend(_check_cv(self._df, reference, self._config))
        cv_issues.extend(_check_cv(self._df, test, self._config))
        if cv_issues:
            msg = (
                "High CV detected - FDA guidance recommends CV <= 20% at early "
                "timepoints (<=15 min) and CV <= 10% at later timepoints:\n  "
                + "\n  ".join(cv_issues)
            )
            persisted.append(msg)
            warnings.warn(msg, UserWarning, stacklevel=2)

        # ICH M13B Step 2: absolute SD > 8% at any time point (not RSD@mean<=60%)
        sd_issues: list[str] = []
        sd_issues.extend(_check_ich_m13b_sd(self._df, reference, self._config))
        sd_issues.extend(_check_ich_m13b_sd(self._df, test, self._config))
        if sd_issues:
            msg = (
                "ICH M13B (Step 2 draft) high variability: absolute SD > 8% at one "
                "or more time points (use bootstrap f2 CI when SD > 8%):\n  "
                + "\n  ".join(sd_issues)
            )
            persisted.append(msg)
            warnings.warn(msg, UserWarning, stacklevel=2)

        f1_value = f1(ref_means, tst_means)
        f2_value = f2(ref_means, tst_means, method=f2_method)  # type: ignore[arg-type]

        # n_timepoints after regulatory trimming may differ from input length
        n_used = len(ref_times)
        if f2_method == "regulatory":
            cutoff = len(ref_means)
            for i, (r, t) in enumerate(zip(ref_means, tst_means, strict=True)):
                if r > 85.0 and t > 85.0:
                    cutoff = i + 1
                    break
            n_used = cutoff

        if f2_method == "all_points":
            persisted.append(
                "f2_method='all_points' was used. FDA-supporting similarity claims "
                "require f2_method='regulatory' (85% rule) and documented prerequisites."
            )

        return ComparisonResult(
            reference_label=reference,
            test_label=test,
            f1_value=f1_value,
            f2_value=f2_value,
            n_timepoints=n_used,
            reference_mean=ref_means,
            test_mean=tst_means,
            time_points=ref_times,
            f2_method=f2_method,
            warnings=persisted,
        )

    def bootstrap_compare(
        self,
        reference: str,
        test: str,
        *,
        n_replicates: int = 5000,
        confidence_level: float = 0.90,
        seed: int | None = None,
    ) -> BootstrapF2Result:
        """Compare two formulations using bootstrap f2 confidence interval.

        Extracts vessel-level data from the loaded CSV and calls bootstrap_f2.
        Suitable for small samples where fewer than 12 vessels are available.

        Parameters
        ----------
        reference : str
            Label of the reference formulation.
        test : str
            Label of the test formulation.
        n_replicates : int, optional
            Number of bootstrap replicates. Default 5000.
        confidence_level : float, optional
            CI level, e.g. 0.90 for 90% CI. Default 0.90.
        seed : int or None, optional
            Random seed for reproducibility.

        Returns
        -------
        BootstrapF2Result
        """
        import numpy as np

        from .bootstrap import bootstrap_f2 as _bootstrap_f2

        available = self.formulations()
        if reference not in available:
            raise ValueError(
                f"Reference formulation '{reference}' not found. Available: {available}"
            )
        if test not in available:
            raise ValueError(f"Test formulation '{test}' not found. Available: {available}")

        cfg = self._config
        df = self._df

        def _vessel_matrix(label: str) -> np.ndarray:
            subset = df[df[cfg.formulation_col] == label].sort_values([cfg.batch_col, cfg.time_col])
            batches = subset[cfg.batch_col].unique()
            rows = []
            for batch in batches:
                batch_data = subset[subset[cfg.batch_col] == batch].sort_values(cfg.time_col)
                rows.append(batch_data[cfg.percent_released_col].values)
            return np.array(rows, dtype=float)

        ref_matrix = _vessel_matrix(reference)
        tst_matrix = _vessel_matrix(test)

        return _bootstrap_f2(
            ref_matrix,
            tst_matrix,
            n_replicates=n_replicates,
            confidence_level=confidence_level,
            seed=seed,
        )

    def fit_models(
        self,
        formulation: str,
        models: list[str] | None = None,
    ) -> DissolutionFitResults:
        """Fit standard dissolution release models to the mean profile of a formulation.

        Parameters
        ----------
        formulation : str
            Label of the formulation to fit.
        models : list[str] or None, optional
            Model names to fit. Defaults to all five standard models:
            ``["zero_order", "first_order", "higuchi", "korsmeyer_peppas", "weibull"]``.

        Returns
        -------
        DissolutionFitResults
            Fit results ranked by AICc. Use ``.best`` for the top-ranked model,
            ``.summary()`` for a ranked table, ``.plot()`` for a profile overlay,
            and ``.report()`` for an HTML report.

        Raises
        ------
        ValueError
            If the formulation label is not found in the dataset.
        """
        from .models import fit_dissolution_models

        available = self.formulations()
        if formulation not in available:
            raise ValueError(f"Formulation '{formulation}' not found. Available: {available}")

        times, means = get_formulation_means(self._df, formulation)
        return fit_dissolution_models(
            time_points=times,
            observed_mean=means,
            formulation_label=formulation,
            models=models,
        )
