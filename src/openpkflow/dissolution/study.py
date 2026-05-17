"""High-level DissolutionStudy API."""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from .loader import DissolutionCSVConfig, get_formulation_means, load_dissolution_csv
from .similarity import f1, f2

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
    """

    reference_label: str
    test_label: str
    f1_value: float
    f2_value: float
    n_timepoints: int
    reference_mean: list[float]
    test_mean: list[float]
    time_points: list[float] = field(default_factory=list)

    def summary(self) -> str:
        """Return a human-readable text summary of the comparison result.

        Returns
        -------
        str
            Multi-line summary including f1, f2, interpretation, and disclaimer.
        """
        interpretation = (
            "f2 >= 50 supports similarity between profiles."
            if self.f2_value >= 50.0
            else "f2 < 50 does not support similarity between profiles."
        )
        lines = [
            "Dissolution Similarity Analysis",
            "================================",
            f"Reference: {self.reference_label}  |  Test: {self.test_label}",
            f"Timepoints: {self.n_timepoints}  |  Method: f1/f2 (FDA 1997 guidance)",
            "",
            f"f1 (difference factor): {self.f1_value:.2f}",
            f"f2 (similarity factor): {self.f2_value:.2f}",
            "",
            f"Interpretation: {interpretation}",
            "",
            "Disclaimer: This output was generated using OpenPKFlow (open-source).",
            "Final regulatory interpretation should be reviewed by qualified experts.",
        ]
        return "\n".join(lines)

    def report(
        self,
        output_path: str | Path,
        format: str = "html",
    ) -> str:
        """Generate a Markdown or HTML report for this comparison result.

        Parameters
        ----------
        output_path : str | Path
            Where to save the report file.
        format : str, optional
            Output format: ``"html"`` or ``"markdown"``. Defaults to ``"html"``.

        Returns
        -------
        str
            The rendered report content.
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
        return cls(df, config)

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

        Returns
        -------
        ComparisonResult
            Computed f1, f2, and associated metadata.

        Raises
        ------
        ValueError
            If either formulation label is not found in the dataset, or if the
            reference and test profiles do not share the same time points.
        """
        available = self.formulations()

        if reference not in available:
            raise ValueError(
                f"Reference formulation '{reference}' not found. "
                f"Available: {available}"
            )
        if test not in available:
            raise ValueError(
                f"Test formulation '{test}' not found. "
                f"Available: {available}"
            )

        ref_times, ref_means = get_formulation_means(self._df, reference)
        tst_times, tst_means = get_formulation_means(self._df, test)

        if ref_times != tst_times:
            raise ValueError(
                f"Reference and test formulations do not share the same time points.\n"
                f"  Reference time points: {ref_times}\n"
                f"  Test time points:      {tst_times}"
            )

        # Regulatory 85% check: warn if more than one timepoint exceeds 85%
        for label, means in ((reference, ref_means), (test, tst_means)):
            n_above_85 = sum(1 for v in means if v > 85.0)
            if n_above_85 > 1:
                warnings.warn(
                    _85_PCT_WARNING % (label, n_above_85),
                    UserWarning,
                    stacklevel=2,
                )

        # CV check per FDA dissolution guidance (CV <= 20% early, <= 10% later)
        cv_issues: list[str] = []
        cv_issues.extend(_check_cv(self._df, reference, self._config))
        cv_issues.extend(_check_cv(self._df, test, self._config))
        if cv_issues:
            warnings.warn(
                "High CV detected - FDA guidance recommends CV <= 20% at early "
                "timepoints (<=15 min) and CV <= 10% at later timepoints:\n  "
                + "\n  ".join(cv_issues),
                UserWarning,
                stacklevel=2,
            )

        f1_value = f1(ref_means, tst_means)
        f2_value = f2(ref_means, tst_means)

        return ComparisonResult(
            reference_label=reference,
            test_label=test,
            f1_value=f1_value,
            f2_value=f2_value,
            n_timepoints=len(ref_times),
            reference_mean=ref_means,
            test_mean=tst_means,
            time_points=ref_times,
        )
