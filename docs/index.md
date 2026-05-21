# OpenPKFlow

**A transparent, reproducible, open-source Python workflow for dissolution, NCA, PK/PD simulation, and pharmacometric reporting.**

[![CI](https://github.com/priyamthakar/openpkflow/actions/workflows/ci.yml/badge.svg)](https://github.com/priyamthakar/openpkflow/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/openpkflow)](https://pypi.org/project/openpkflow/)
[![Python](https://img.shields.io/pypi/pyversions/openpkflow)](https://pypi.org/project/openpkflow/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/priyamthakar/openpkflow/blob/main/LICENSE)

---

## What it does

OpenPKFlow gives formulation scientists, PK/PD researchers, and CRO/CDMO teams a clean Python workflow for:

| Module | What it covers |
|--------|---------------|
| `dissolution` | f1, f2, bootstrap f2, Weibull/Higuchi/KP/first-order/zero-order model fitting |
| `nca` | AUClast, AUCinf, Cmax, Tmax, lambda\_z, t1/2, CL/F, Vz/F — three AUC methods, explicit BLQ |
| `sim` | 1- and 2-compartment IV bolus/infusion/oral, repeated dosing, superposition |
| `pop` | GOF plots (4-panel), VPC with percentile bands, NONMEM-style dataset helpers |
| `report` | Markdown, HTML, PDF (ReportLab), Word (python-docx) |
| `ml` | Experimental torch MLP surrogate for 1-cmt oral profiles |
| `validation` | Utility functions for cross-checking against reference values |

It does not replace expert regulatory judgement or validated commercial platforms.
It makes routine analysis faster, cleaner, and more reproducible.

---

## Install

```bash
pip install openpkflow
```

For PDF and Word reports:

```bash
pip install openpkflow[reports]
```

For ML surrogate (torch):

```bash
pip install openpkflow[ml]
```

---

## Quick example

```python
from openpkflow.dissolution import f1, f2

reference = [20.0, 40.0, 60.0, 80.0, 90.0]
test      = [21.0, 39.0, 61.0, 79.0, 88.0]

print(f"f1 = {f1(reference, test):.2f}")   # 1.33
print(f"f2 = {f2(reference, test):.2f}")   # 72.80
```

See the [Tutorials](tutorials/dissolution.md) section for complete worked examples.

---

## Philosophy

OpenPKFlow is **report-first**: every analysis ends in a clean, shareable output — HTML, PDF, or Word — suitable for supervisors, clients, CROs, and regulatory teams. Calculation correctness is necessary but not sufficient.

> This package is open-source. Final regulatory interpretation should be reviewed by qualified formulation, pharmacokinetic, and regulatory experts.
