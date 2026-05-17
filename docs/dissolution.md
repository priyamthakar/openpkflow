# Dissolution Module

## Overview

Dissolution similarity analysis compares drug release profiles between a reference
and a test formulation. It is a core tool in formulation development and regulatory
submissions for scale-up, post-approval changes (SUPAC), and biowaiver applications.

OpenPKFlow provides:

- **f1** and **f2** as standalone functions for quick comparisons.
- A `DissolutionStudy` class (v0.1.x) that handles multi-batch CSV data, batch
  averaging, and report generation.
- Bootstrap confidence intervals for f2 (v0.2.0, planned).
- Weibull / first-order / Korsmeyer-Peppas model fitting (v0.2.0, planned).

---

## f1 — Difference Factor

### Formula

```
        n
       sum |Rt - Tt|
       t=1
f1 = -------------- x 100
        n
       sum Rt
       t=1
```

Where `Rt` is the mean percent released for the reference at time point `t`, and
`Tt` is the mean percent released for the test at time point `t`.

### When to use

Use f1 as a supplementary measure alongside f2. f1 is sensitive to both the magnitude
and direction of differences; however, it lacks the statistical properties needed for
regulatory acceptance on its own.

### Regulatory context

The FDA 1997 guidance (*Dissolution Testing of Immediate Release Solid Oral Dosage
Forms*) states that f1 values between 0 and 15 indicate similarity between the two
dissolution profiles.

---

## f2 — Similarity Factor

### Formula

```
             /         1     n              \
f2 = 50 log |  100 / |/  1 + -- sum (Rt-Tt)^2  |
             \              n t=1            /
```

Equivalently:

```python
import math

def f2(ref, test):
    n = len(ref)
    mse = sum((r - t) ** 2 for r, t in zip(ref, test)) / n
    return 50.0 * math.log10(100.0 / math.sqrt(1.0 + mse))
```

### When to use

f2 is the primary regulatory metric for dissolution profile comparison. Use it
whenever you need to demonstrate that a post-approval change has not meaningfully
altered drug release, or to support a biowaiver for a lower strength.

### Regulatory context

- FDA 1997 guidance: **f2 >= 50** is the acceptance threshold (equivalent to an
  average difference of no more than 10% at all time points).
- EMA guideline on dissolution profile comparison (*CPMP/EWP/QWP/1401/98 Rev. 1*):
  same f2 >= 50 threshold.
- At least **12 individual units** per formulation are recommended; mean values are
  used in the calculation.
- f2 should be calculated only at time points where the mean reference value is
  between 1% and 85% released (do not include the plateau region).
- If two or more time points exceed 85% for both profiles, use only one of those
  time points.

---

## Input Requirements

| Requirement | Detail |
|---|---|
| Matched time points | Identical time points for reference and test; no interpolation |
| Percent released values | Must be in the range 0 to 100 |
| Minimum time points | At least 3 (FDA recommendation) |
| Upper plateau cutoff | Exclude time points where both means exceed 85% (use at most one) |
| Replication | At least 12 units per formulation; input means to f1/f2 |
| No interpolation | Caller is responsible for ensuring time points match exactly |

---

## Quick Start

```python
import math
from openpkflow.datasets import EXAMPLE_DISSOLUTION_CSV

# -- Standalone f1 / f2 (pure Python) -----------------------------------

def f1(ref: list[float], test: list[float]) -> float:
    return 100.0 * sum(abs(r - t) for r, t in zip(ref, test)) / sum(ref)

def f2(ref: list[float], test: list[float]) -> float:
    n = len(ref)
    mse = sum((r - t) ** 2 for r, t in zip(ref, test)) / n
    return 50.0 * math.log10(100.0 / math.sqrt(1.0 + mse))

ref  = [15.0, 30.0, 48.0, 62.0, 78.0, 90.0]
test = [12.1, 24.0, 40.0, 55.0, 70.1, 82.1]

print(f"f1 = {f1(ref, test):.2f}")   # e.g. 12.34
print(f"f2 = {f2(ref, test):.2f}")   # e.g. 57.8


# -- DissolutionStudy (requires dissolution module, v0.1.x) -------------

from openpkflow.dissolution import DissolutionStudy

study  = DissolutionStudy.from_csv(EXAMPLE_DISSOLUTION_CSV)
result = study.compare(reference="reference", test="test")

print(result.summary())
result.to_html("output/dissolution_report.html")
```

---

## CSV Format

The bundled example CSV and any user-supplied CSV must follow this structure:

```csv
formulation,batch,time,percent_released
reference,R1,5,14.2
reference,R1,10,29.1
...
test,T1,5,11.5
test,T1,10,23.4
...
```

| Column | Type | Description |
|---|---|---|
| `formulation` | string | Label for the formulation (e.g. `"reference"`, `"test"`) |
| `batch` | string | Batch or unit identifier |
| `time` | numeric | Time point in minutes (or hours — be consistent) |
| `percent_released` | numeric | Cumulative percent drug released (0 to 100) |

The bundled example dataset can be loaded with:

```python
import pandas as pd
from openpkflow.datasets import EXAMPLE_DISSOLUTION_CSV

df = pd.read_csv(EXAMPLE_DISSOLUTION_CSV)
```

---

## API Reference

| Symbol | Module | Description |
|---|---|---|
| `f1(ref, test)` | `openpkflow.dissolution` | Difference factor |
| `f2(ref, test)` | `openpkflow.dissolution` | Similarity factor |
| `DissolutionStudy` | `openpkflow.dissolution` | High-level study object (v0.1.x) |
| `ComparisonResult` | `openpkflow.dissolution` | Result of a profile comparison (v0.1.x) |
| `EXAMPLE_DISSOLUTION_CSV` | `openpkflow.datasets` | Path to the bundled example CSV |

---

## Validation

The f2 implementation in OpenPKFlow has been manually cross-checked against:

- The worked examples in the **FDA 1997 guidance** document (CDER).
- The **R `bootf2` package** (Liao & Duong, CRAN) for the standard f2 formula.
- The EMA CPMP/EWP/QWP/1401/98 Rev. 1 guideline examples.

Bootstrap f2 confidence intervals (planned for v0.2.0) will follow the
Mandula/Shah (1998) bootstrap procedure as implemented in `bootf2`.

If you identify a discrepancy, please open an issue at
<https://github.com/priyamthakar1/openpkflow/issues>.

---

## Disclaimer

OpenPKFlow is a scientific computing tool intended for research and educational
purposes. It is not a validated regulatory submission tool. All outputs must be
reviewed and interpreted by qualified professionals before use in regulatory filings.
The f1 and f2 calculations follow published FDA and EMA guidance but do not
substitute for official regulatory advice.
