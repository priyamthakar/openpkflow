"""Basic dissolution similarity analysis with OpenPKFlow.

Run this example from the repo root after installing the package::

    pip install -e .
    python examples/dissolution_basic.py

Or without installing (editable source on sys.path)::

    python -c "import sys; sys.path.insert(0, 'src')" && python examples/dissolution_basic.py
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parent.parent
_src = _repo_root / "src"
if _src.exists() and str(_src) not in sys.path:
    sys.path.insert(0, str(_src))


print("=" * 62)
print("  OpenPKFlow -- Basic Dissolution Similarity Example")
print("=" * 62)
print()

from openpkflow.datasets import EXAMPLE_DISSOLUTION_CSV  # noqa: E402

try:
    import pandas as pd

    df = pd.read_csv(EXAMPLE_DISSOLUTION_CSV)
    print(f"Loaded dataset: {EXAMPLE_DISSOLUTION_CSV.name}")
    print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")
    print()
    print("First 6 rows:")
    print(df.head(6).to_string(index=False))
    print()
except ImportError:
    print("[WARNING] pandas not installed. Skipping DataFrame preview.\n")

# ---------------------------------------------------------------------------
# Standalone f1 / f2
# ---------------------------------------------------------------------------
REF_MEANS = [15.0, 30.0, 48.0, 62.0, 78.0, 90.0]
TEST_MEANS = [12.1, 24.0, 40.0, 55.0, 70.1, 82.1]
TIME_POINTS = [5, 10, 15, 20, 30, 45]

from openpkflow.dissolution import f1, f2  # noqa: E402

print("-" * 62)
print("  Standalone f1 / f2")
print("-" * 62)
print(f"  Time points (min) : {TIME_POINTS}")
print(f"  Reference means   : {REF_MEANS}")
print(f"  Test means        : {TEST_MEANS}")
print()

f1_val = f1(REF_MEANS, TEST_MEANS)
f2_val = f2(REF_MEANS, TEST_MEANS)

print(f"  f1 = {f1_val:.2f}  (< 15 -> similar)")
print(f"  f2 = {f2_val:.2f}  (>= 50 -> similar)")
print()
if f2_val >= 50:
    print("  Result: profiles are SIMILAR (f2 >= 50)")
else:
    print("  Result: profiles are NOT similar (f2 < 50)")
print()

# ---------------------------------------------------------------------------
# DissolutionStudy high-level API
# ---------------------------------------------------------------------------
print("-" * 62)
print("  DissolutionStudy API")
print("-" * 62)

from openpkflow.dissolution import DissolutionStudy  # noqa: E402

study = DissolutionStudy.from_csv(EXAMPLE_DISSOLUTION_CSV)
result = study.compare(reference="reference", test="test")

print("  Summary:")
print(result.summary())
print()

output_dir = _repo_root / "examples" / "output"
output_dir.mkdir(parents=True, exist_ok=True)
report_path = output_dir / "dissolution_report.html"

result.report(report_path, format="html")
print(f"  HTML report written to: {report_path}")

print()
print("=" * 62)
print("  Done.")
print("=" * 62)
