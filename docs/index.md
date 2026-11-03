# OpenPKFlow

**A transparent, reproducible, open-source Python workflow for dissolution, NCA,
PK/PD simulation, and pharmacometric reporting, backed by executable reference and
analytical tests.**

[![CI](https://github.com/priyamthakar/openpkflow/actions/workflows/ci.yml/badge.svg)](https://github.com/priyamthakar/openpkflow/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/openpkflow)](https://pypi.org/project/openpkflow/)
[![Python](https://img.shields.io/pypi/pyversions/openpkflow)](https://pypi.org/project/openpkflow/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/priyamthakar/openpkflow/blob/main/LICENSE)

---

## What it does

OpenPKFlow gives formulation scientists, PK/PD researchers, and CRO/CDMO teams a Python workflow for:

| Module | What it covers |
|--------|---------------|
| `dissolution` | f1, f2, bootstrap f2, MSD, max deviation, model-dependent comparison, multi-media, SUPAC screening, alcohol dose-dumping f2, model fitting |
| `nca` | AUClast, AUCinf, Cmax, Tmax, lambda\_z, t1/2, CL/F, Vz/F; three AUC methods, explicit BLQ, %AUCextrap flag, C0 back-extrapolation, DN params, CDISC PP, plus model-informed sparse oral screening |
| `be` | Paired 2x2 TOST, formal complete balanced TR/RT 2x2 ANOVA, validated balanced FDA partial-replicate RSABE, power / sample size, and separate research-grade replicate screening |
| `bayes` | MAP individual PK (scipy), full Bayesian posterior (PyMC), Bayesian 2x2 crossover BE |
| `pop` | FOCE-I and SAEM estimation (1/2-cmt; frozen for extension), GOF plots, VPC, NONMEM-style dataset helpers |
| `sim` | 1- and 2-compartment IV bolus/infusion/oral, transit absorption, steady-state metrics, repeated dosing, superposition |
| `ivivc` | Level A (Wagner-Nelson, Loo-Riegelman, convolution, Levy, %PE) plus Level B/C MDT/MRT helpers |
| `pipeline` | Multi-stage study orchestration (dissolution + NCA + BE) with unified reports and reproducibility audit bundles |
| `report` | Markdown, HTML, PDF (ReportLab), Word (python-docx) |
| `ml` | Experimental torch MLP surrogate for 1-cmt oral profiles |
| `validation` | Utility functions for cross-checking against reference values |

It does not replace expert regulatory judgement or validated commercial platforms.

The latest release is v2.10.0 (2026-11-03). It adds `to_dict()` to every public
result object, `to_dataframe()` to the table-shaped ones, and attribute access to
subpackages after `import openpkflow`, without changing any calculation; see the
[Changelog](changelog.md). The hosted web demo runs on a free Render instance
that sleeps when idle, so the first request after a pause can be slow. It is a
demo, not a production service.

## What it is and is not

OpenPKFlow is a transparent Python toolkit for exploratory and reproducible
pharmacometric workflows: dissolution comparison, NCA, simulation,
bioequivalence screening, IVIVC, population PK diagnostics, and report
generation.

OpenPKFlow is not a substitute for qualified regulatory judgement, validated
commercial platforms, or jurisdiction-specific submission workflows. The FDA
partial-replicate implementation is validated only for complete balanced
TRR/RTR/RRT allocation against Patterson and Jones (2012), Table II. General
replicate bioequivalence screening and research-grade PopPK remain
decision-support and require independent jurisdiction-specific review.

Full scope language, pipeline focus, PopPK / RSABE validation boundaries, and validation
links: [Positioning](positioning.md).

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

print(f"f1 = {f1(reference, test):.2f}")   # 2.07
print(f"f2 = {f2(reference, test):.2f}")   # 89.63
```

See the [Tutorials](tutorials/dissolution.md) section for complete worked examples.

---

## Documentation

- **[Theory Guide](theory.md)**: formula derivations for NCA, simulation, dissolution, IVIVC, BE, population PK and Bayesian PK
- **[Migration Guide](migration-cheatsheet.md)**: WinNonlin, NONMEM and R names mapped to OpenPKFlow
- **[Tutorials](tutorials/dissolution.md)**: worked examples for each analysis workflow
- **[Validation Matrix](validation-matrix.md)**: external comparators and the tests that pin them
- **[Validation API](reference/validation.md)**: bias, RMSE and percent-tolerance helpers
- **[API Reference](reference/dissolution.md)**: functions and classes in the public analysis modules

---

## Philosophy

OpenPKFlow is **report-first**: every analysis result object has a `.report()` method. All of them write HTML and Markdown; the dissolution, NCA, simulation, IVIVC, Bayesian and population PK diagnostic reports also write PDF and Word with the `[reports]` extra, while the bioequivalence and PopPK estimation reports are HTML and Markdown only.

> This package is open-source. Final regulatory interpretation should be reviewed by qualified formulation, pharmacokinetic, and regulatory experts.
