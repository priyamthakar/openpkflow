"""Advanced dissolution similarity analysis with OpenPKFlow.

Demonstrates:
- Loading the bundled CSV dataset
- Inspecting available formulations
- Computing f1/f2 manually from averaged batch data
- Exporting results as a dict
- Forthcoming features in v0.2.0

Run from the repo root after installing the package::

    pip install -e .
    python examples/dissolution_advanced.py
"""

from __future__ import annotations

import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Ensure the package is importable when running from the repo root without
# a prior `pip install -e .`.
# ---------------------------------------------------------------------------
_repo_root = Path(__file__).resolve().parent.parent
_src = _repo_root / "src"
if _src.exists() and str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from openpkflow.datasets import EXAMPLE_DISSOLUTION_CSV  # noqa: E402

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
print("=" * 62)
print("  OpenPKFlow -- Advanced Dissolution Example")
print("=" * 62)
print()

# ---------------------------------------------------------------------------
# 1. Load CSV and inspect available formulations
# ---------------------------------------------------------------------------
try:
    import pandas as pd  # type: ignore[import]

    _HAS_PANDAS = True
except ImportError:
    _HAS_PANDAS = False

if _HAS_PANDAS:
    df = pd.read_csv(EXAMPLE_DISSOLUTION_CSV)
    formulations = sorted(df["formulation"].unique())
    print("Formulations in dataset:")
    for f in formulations:
        batches = sorted(df.loc[df["formulation"] == f, "batch"].unique())
        times = sorted(df.loc[df["formulation"] == f, "time"].unique())
        print(f"  {f!r}  batches={batches}  time points={list(times)}")
    print()
else:
    print("[WARNING] pandas not installed; loading CSV manually.\n")

# ---------------------------------------------------------------------------
# Minimal CSV reader (no pandas dependency) for the averaged-data path
# ---------------------------------------------------------------------------


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    """Read a CSV file into a list of row dicts (stdlib only)."""
    import csv

    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


rows = _read_csv_rows(EXAMPLE_DISSOLUTION_CSV)

# ---------------------------------------------------------------------------
# 2. Average across batches per (formulation, time)
# ---------------------------------------------------------------------------

# accumulate: {formulation: {time: [values]}}
accum: dict[str, dict[float, list[float]]] = defaultdict(lambda: defaultdict(list))
for row in rows:
    accum[row["formulation"]][float(row["time"])].append(float(row["percent_released"]))

# compute means
means: dict[str, dict[float, float]] = {}
for form, time_map in accum.items():
    means[form] = {t: sum(vals) / len(vals) for t, vals in sorted(time_map.items())}

print("-" * 62)
print("  Mean percent released by formulation and time point")
print("-" * 62)
header = f"  {'Time (min)':>10}" + "".join(f"  {f:>15}" for f in sorted(means))
print(header)
all_times = sorted(next(iter(means.values())).keys())
for t in all_times:
    row_str = f"  {t:>10.0f}"
    for form in sorted(means):
        row_str += f"  {means[form][t]:>15.2f}"
    print(row_str)
print()

# ---------------------------------------------------------------------------
# 3. Manual f1 / f2 from averaged data
# ---------------------------------------------------------------------------


def f1(ref: list[float], test: list[float]) -> float:
    """Difference factor (FDA 1997).

    Parameters
    ----------
    ref:
        Reference mean percent released at each matched time point.
    test:
        Test mean percent released at each matched time point.

    Returns
    -------
    float
        f1 value; values < 15 indicate similarity.

    Raises
    ------
    ValueError
        If ref and test have different lengths or ref sum is zero.
    """
    if len(ref) != len(test):
        raise ValueError(f"Length mismatch: ref has {len(ref)}, test has {len(test)}.")
    den = sum(ref)
    if den == 0:
        raise ValueError("Sum of reference values is zero; cannot compute f1.")
    return 100.0 * sum(abs(r - t) for r, t in zip(ref, test, strict=False)) / den


def f2(ref: list[float], test: list[float]) -> float:
    """Similarity factor (FDA 1997).

    Parameters
    ----------
    ref:
        Reference mean percent released at each matched time point.
    test:
        Test mean percent released at each matched time point.

    Returns
    -------
    float
        f2 value; values >= 50 indicate similarity.

    Raises
    ------
    ValueError
        If ref and test have different lengths.
    """
    if len(ref) != len(test):
        raise ValueError(f"Length mismatch: ref has {len(ref)}, test has {len(test)}.")
    n = len(ref)
    mse = sum((r - t) ** 2 for r, t in zip(ref, test, strict=False)) / n
    return 50.0 * math.log10(100.0 / math.sqrt(1.0 + mse))


ref_vals = [means["reference"][t] for t in all_times]
test_vals = [means["test"][t] for t in all_times]

f1_val = f1(ref_vals, test_vals)
f2_val = f2(ref_vals, test_vals)

print("-" * 62)
print("  f1 / f2 computed from batch-averaged means")
print("-" * 62)
print(f"  f1 = {f1_val:.3f}  (acceptance: < 15)")
print(f"  f2 = {f2_val:.3f}  (acceptance: >= 50)")
print()
similarity = "SIMILAR" if f2_val >= 50 else "NOT SIMILAR"
print(f"  Conclusion (f2 criterion): profiles are {similarity}")
print()

# ---------------------------------------------------------------------------
# 4. Export results as a dict
# ---------------------------------------------------------------------------


def _comparison_as_dict(
    *,
    reference_formulation: str,
    test_formulation: str,
    time_points: list[float],
    ref_means: list[float],
    test_means: list[float],
    f1_value: float,
    f2_value: float,
) -> dict[str, Any]:
    """Package comparison results into a plain dict for serialisation.

    Parameters
    ----------
    reference_formulation:
        Name of the reference formulation.
    test_formulation:
        Name of the test formulation.
    time_points:
        Matched time points used in the comparison.
    ref_means:
        Batch-averaged reference values.
    test_means:
        Batch-averaged test values.
    f1_value:
        Computed f1.
    f2_value:
        Computed f2.

    Returns
    -------
    dict[str, Any]
        Flat, JSON-serialisable result dict.
    """
    return {
        "reference_formulation": reference_formulation,
        "test_formulation": test_formulation,
        "time_points_min": time_points,
        "reference_means_pct": [round(v, 4) for v in ref_means],
        "test_means_pct": [round(v, 4) for v in test_means],
        "f1": round(f1_value, 4),
        "f2": round(f2_value, 4),
        "f1_similar": f1_value < 15,
        "f2_similar": f2_value >= 50,
    }


result_dict = _comparison_as_dict(
    reference_formulation="reference",
    test_formulation="test",
    time_points=all_times,
    ref_means=ref_vals,
    test_means=test_vals,
    f1_value=f1_val,
    f2_value=f2_val,
)

print("-" * 62)
print("  Results dict (ready for JSON / database export)")
print("-" * 62)
for key, val in result_dict.items():
    print(f"  {key:<30} {val!r}")
print()

# ---------------------------------------------------------------------------
# 5. Serialise to JSON (stdlib only)
# ---------------------------------------------------------------------------
import json  # noqa: E402 (stdlib)

json_path = _repo_root / "examples" / "output" / "dissolution_results.json"
json_path.parent.mkdir(parents=True, exist_ok=True)
json_path.write_text(json.dumps(result_dict, indent=2), encoding="utf-8")
print(f"  Results saved to: {json_path}")
print()

# ---------------------------------------------------------------------------
# 6. Forthcoming features note
# ---------------------------------------------------------------------------
print("-" * 62)
print("  Coming in v0.2.0")
print("-" * 62)
print(
    "  bootstrap_f2(ref, test, n_boot=10_000)\n"
    "    Bootstrap confidence interval for f2 (Shah et al. 1998\n"
    "    / Mandula 2005 approach).\n"
    "\n"
    "  fit_dissolution_model(times, pct_released, model='weibull')\n"
    "    Fit Weibull, first-order, or Korsmeyer-Peppas models to\n"
    "    individual dissolution profiles and return fitted parameters\n"
    "    with goodness-of-fit statistics.\n"
    "\n"
    "  DissolutionStudy.from_csv(path)\n"
    "    High-level study object with automatic batch averaging,\n"
    "    model fitting, and HTML / Excel report generation.\n"
)

print("=" * 62)
print("  Done.")
print("=" * 62)
