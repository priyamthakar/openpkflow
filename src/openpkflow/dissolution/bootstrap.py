"""Bootstrap f2 confidence interval for dissolution similarity.

References:
    Shah VP et al. (1998) In vitro dissolution profile comparison —
    statistics and analysis of the similarity factor, f2.
    Pharm Res, 15(6):889–896.

    Davit BM et al. (2013) Comparing dissolution profiles —
    recommendations for regulatory discussions.
    AAPS J, 15(4):1150–1157.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np

from .similarity import f2 as _f2


@dataclass(frozen=True)
class BootstrapF2Result:
    """Result of a bootstrap f2 analysis."""

    f2_observed: float
    ci_lower: float
    ci_upper: float
    n_replicates: int
    confidence_level: float
    n_timepoints: int
    n_reference_vessels: int
    n_test_vessels: int

    @property
    def is_similar(self) -> bool:
        """True if lower bound of CI >= 50."""
        return self.ci_lower >= 50.0

    def summary(self) -> str:
        """Return a human-readable summary of the bootstrap f2 result.

        Returns
        -------
        str
            Multi-line summary string.
        """
        pct = int(self.confidence_level * 100)
        verdict = "SIMILAR" if self.is_similar else "NOT SIMILAR"
        lines = [
            "Bootstrap f2 Analysis",
            f"  Observed f2:       {self.f2_observed:.2f}",
            f"  {pct}% CI:             [{self.ci_lower:.2f}, {self.ci_upper:.2f}]",
            (
                f"  Verdict:           {verdict} (CI lower bound >= 50)"
                if self.is_similar
                else f"  Verdict:           {verdict} (CI lower bound < 50)"
            ),
            f"  Replicates:        {self.n_replicates}",
            f"  Timepoints:        {self.n_timepoints}",
            f"  Reference vessels: {self.n_reference_vessels}",
            f"  Test vessels:      {self.n_test_vessels}",
            "",
            "Note: Bootstrap f2 is suitable when <12 vessels are available.",
            "Regulatory acceptance requires expert interpretation.",
        ]
        return "\n".join(lines)


def bootstrap_f2(
    reference: np.ndarray,
    test: np.ndarray,
    *,
    n_replicates: int = 5000,
    confidence_level: float = 0.90,
    seed: int | None = None,
) -> BootstrapF2Result:
    """Compute bootstrap f2 confidence interval.

    Parameters
    ----------
    reference : np.ndarray
        2-D array of shape (n_vessels, n_timepoints). Each row is one vessel.
    test : np.ndarray
        2-D array of shape (n_vessels, n_timepoints). Each row is one vessel.
    n_replicates : int
        Number of bootstrap replicates. Default 5000.
    confidence_level : float
        CI level, e.g. 0.90 for 90% CI. Default 0.90.
    seed : int or None
        Random seed for reproducibility.

    Returns
    -------
    BootstrapF2Result
        Observed f2, CI bounds, and metadata.

    Raises
    ------
    ValueError
        If arrays are not 2-D, have mismatched timepoints, fewer than 3 timepoints,
        or fewer than 2 vessels in either group.
    """
    reference = np.asarray(reference, dtype=float)
    test = np.asarray(test, dtype=float)

    if reference.ndim != 2:
        raise ValueError("reference must be a 2-D array (n_vessels, n_timepoints)")
    if test.ndim != 2:
        raise ValueError("test must be a 2-D array (n_vessels, n_timepoints)")
    if reference.shape[1] != test.shape[1]:
        raise ValueError(
            f"reference and test must have the same number of timepoints, "
            f"got {reference.shape[1]} and {test.shape[1]}"
        )

    n_ref, n_tp = reference.shape
    n_tst = test.shape[0]

    if n_tp < 3:
        raise ValueError("At least 3 timepoints are required for f2 calculation.")
    if n_ref < 2:
        raise ValueError("At least 2 reference vessels are required for bootstrap.")
    if n_tst < 2:
        raise ValueError("At least 2 test vessels are required for bootstrap.")

    if n_ref >= 12 or n_tst >= 12:
        warnings.warn(
            "Bootstrap f2 is designed for small samples (<12 vessels). "
            "With n>=12, the regulatory single-point f2 is preferred.",
            UserWarning,
            stacklevel=2,
        )

    # Compute observed f2 from column means
    ref_mean = reference.mean(axis=0)
    tst_mean = test.mean(axis=0)
    f2_observed = _f2(ref_mean.tolist(), tst_mean.tolist())

    rng = np.random.default_rng(seed)
    f2_boots = np.empty(n_replicates)

    for i in range(n_replicates):
        ref_boot = reference[rng.integers(0, n_ref, size=n_ref)].mean(axis=0)
        tst_boot = test[rng.integers(0, n_tst, size=n_tst)].mean(axis=0)
        f2_boots[i] = _f2(ref_boot.tolist(), tst_boot.tolist())

    alpha = 1.0 - confidence_level
    ci_lower = float(np.percentile(f2_boots, 100 * alpha / 2))
    ci_upper = float(np.percentile(f2_boots, 100 * (1 - alpha / 2)))

    return BootstrapF2Result(
        f2_observed=f2_observed,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        n_replicates=n_replicates,
        confidence_level=confidence_level,
        n_timepoints=n_tp,
        n_reference_vessels=n_ref,
        n_test_vessels=n_tst,
    )
