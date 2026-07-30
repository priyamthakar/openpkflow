# OpenPKFlow

**A transparent, reproducible, open-source Python workflow for dissolution, NCA,
PK/PD simulation, and pharmacometric reporting, backed by executable reference and
analytical tests with report-first documentation.**

[![CI](https://github.com/priyamthakar/openpkflow/actions/workflows/ci.yml/badge.svg)](https://github.com/priyamthakar/openpkflow/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/openpkflow)](https://pypi.org/project/openpkflow/)
[![Python](https://img.shields.io/pypi/pyversions/openpkflow)](https://pypi.org/project/openpkflow/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/priyamthakar/openpkflow/blob/main/LICENSE)

---

## What it does

OpenPKFlow gives formulation scientists, PK/PD researchers, and CRO/CDMO teams a clean Python workflow for:

| Module | What it covers |
|--------|---------------|
| `dissolution` | f1, f2, bootstrap f2, MSD, max deviation, model-dependent comparison, multi-media, SUPAC screening, alcohol dose-dumping f2, model fitting |
| `nca` | AUClast, AUCinf, Cmax, Tmax, lambda\_z, t1/2, CL/F, Vz/F — three AUC methods, explicit BLQ, %AUCextrap flag, C0 back-extrapolation, DN params, CDISC PP, plus model-informed sparse oral screening |
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
It makes routine analysis faster, cleaner, and more reproducible.

Current release and takeover status are maintained in the repository-root
`HANDOFF.md`. The latest public release is v2.8.0, published on 2026-07-30.
Public installation and hosted version/commit convergence are verified. The
release includes the Advanced Dissolution Workbench.

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

print(f"f1 = {f1(reference, test):.2f}")   # 1.33
print(f"f2 = {f2(reference, test):.2f}")   # 72.80
```

See the [Tutorials](tutorials/dissolution.md) section for complete worked examples.

---

## Documentation

- **[Theory Guide](theory.md)** — Full LaTeX formula derivations for every module
- **[Migration Guide](migration-cheatsheet.md)** — WinNonlin / NONMEM / R quick-reference mapping
- **[Tutorials](tutorials/dissolution.md)** — Step-by-step worked examples for supported analysis workflows
- **[Validation Matrix](validation-matrix.md)** — External comparators and executable reference tests
- **[Validation API](reference/validation.md)** — Bias, RMSE, and percent-tolerance helper reference
- **[API Reference](reference/dissolution.md)** — Function and class reference across public analysis modules

---

## Philosophy

OpenPKFlow is **report-first**: every analysis ends in a clean, shareable output — HTML, PDF, or Word — suitable for supervisors, clients, CROs, and regulatory teams. Calculation correctness is necessary but not sufficient.

> This package is open-source. Final regulatory interpretation should be reviewed by qualified formulation, pharmacokinetic, and regulatory experts.
