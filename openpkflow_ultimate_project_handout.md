# OpenPKFlow — Ultimate Project Handout

**Project:** Python-first pharmacometrics, dissolution, NCA, PK/PD simulation, and report-generation toolkit  
**Working package name:** `openpkflow`  
**Target install command:** `pip install openpkflow`  
**Primary user:** Formulation scientists, PK/PD researchers, academic labs, CRO/CDMO teams, and open-source pharmacometrics users  
**Core idea:** Bring the workflow strengths of mature R pharmacometrics packages into a clean, Python-first package, while adding Python's strengths in automation, ML/DL, Bayesian modelling, dashboards, and reproducible reporting.

---

## 1. Executive Summary

OpenPKFlow should not be framed as “Python replacing R” or “Python replacing Certara.” That positioning is too risky and not fully accurate.

The stronger framing is:

> **OpenPKFlow is a Python-first open pharmacometrics and formulation-analysis toolkit for dissolution similarity, NCA, PK/PD simulation, model diagnostics, and regulatory-style report generation.**

R is currently stronger in pharmacometrics because it has mature, domain-specific packages such as:

- `PKNCA` for non-compartmental analysis
- `bootf2` for bootstrap f2 dissolution similarity
- `nlmixr2` for population PK/PD nonlinear mixed-effects modelling
- `mrgsolve` and `rxode2` for ODE-based PK/PD simulation
- `xpose` for NONMEM and NLME diagnostic plotting

Python is stronger for:

- automation
- web applications
- machine learning
- deep learning
- Bayesian modelling with PyMC/Stan
- neural ODE workflows
- report pipelines
- dashboard integration
- scientific software engineering

Therefore, the opportunity is to create a **unified Python workflow layer** that gives formulation and PK scientists a clean, report-ready experience.

---

## 2. Strategic Positioning

### Weak positioning

> “A Python alternative to Certara.”

This sounds like an overclaim and invites regulatory skepticism.

### Better positioning

> **A transparent, reproducible, open-source Python workflow for dissolution, NCA, PK/PD simulation, and pharmacometric reporting.**

### Best PHARAXIS-style positioning

> **PHARAXIS OpenPKFlow Engine combines validated pharmacometric calculations, clean reporting, and Python-based automation to support formulation and PK decision-making. It does not replace expert judgement or validated enterprise platforms; it makes routine analysis faster, cleaner, and more reproducible.**

---

## 3. Real Market Gap

Many formulation scientists already calculate f2, NCA parameters, or simple PK profiles using tools such as:

- Excel
- DDSolver
- GraphPad Prism
- Phoenix WinNonlin
- SAS
- R scripts
- manual templates

The client usually does not pay only for the number. They pay for:

- clean plots
- reproducible calculation
- defensible assumptions
- clear interpretation
- export-ready tables
- professional reports
- fewer spreadsheet errors
- faster decision-making

Therefore, OpenPKFlow must be more than a formula package.

It should be:

> **Calculation engine + validation layer + visualization layer + interpretation layer + report generator.**

---

## 4. Product Vision

OpenPKFlow should eventually combine:

```text
DDSolver-like dissolution analysis
PKNCA-like NCA
mrgsolve/rxode2-like simulation convenience
xpose-like diagnostics
Pharmpy integration
PyMC/Stan Bayesian workflows
torchdiffeq neural ODE modelling
clean regulatory-style report generation
```

The long-term vision:

> **A Python-first open pharmacometrics and formulation informatics platform.**

---

## 5. Recommended Development Order

Do not start with full population PK/NLME. That is the hardest part.

Build in this order:

```text
1. Dissolution f1/f2 + bootstrap f2
2. Dissolution model fitting
3. Report generator
4. NCA engine
5. PK/PD simulation
6. Population PK diagnostics
7. Pharmpy bridge
8. Bayesian PK
9. ML/neural ODE layer
```

The first commercially useful product should be:

> **A Python tool that takes dissolution data and generates a clean f1/f2 + bootstrap f2 + model-fitting report.**

---

## 6. Core Package Architecture

Recommended package structure:

```text
openpkflow/
│
├── pyproject.toml
├── README.md
├── LICENSE
├── CHANGELOG.md
├── CITATION.cff
├── docs/
├── tests/
├── examples/
│
└── src/
    └── openpkflow/
        │
        ├── __init__.py
        ├── cli.py
        │
        ├── dissolution/
        │   ├── __init__.py
        │   ├── similarity.py
        │   ├── bootstrap.py
        │   ├── models.py
        │   ├── plotting.py
        │   └── reporting.py
        │
        ├── nca/
        │   ├── __init__.py
        │   ├── auc.py
        │   ├── lambda_z.py
        │   ├── parameters.py
        │   ├── tables.py
        │   └── reporting.py
        │
        ├── sim/
        │   ├── __init__.py
        │   ├── compartments.py
        │   ├── dosing.py
        │   ├── ode.py
        │   ├── population.py
        │   └── plotting.py
        │
        ├── pop/
        │   ├── __init__.py
        │   ├── datasets.py
        │   ├── diagnostics.py
        │   ├── vpc.py
        │   ├── covariates.py
        │   └── pharmpy_bridge.py
        │
        ├── bayes/
        │   ├── __init__.py
        │   ├── pymc_models.py
        │   ├── stan_export.py
        │   └── posterior_summary.py
        │
        ├── ml/
        │   ├── __init__.py
        │   ├── features.py
        │   ├── predictors.py
        │   ├── neural_ode.py
        │   └── uncertainty.py
        │
        ├── report/
        │   ├── __init__.py
        │   ├── templates/
        │   ├── pdf.py
        │   ├── html.py
        │   └── docx.py
        │
        ├── datasets/
        │   ├── example_dissolution.csv
        │   ├── example_pk_single_dose.csv
        │   └── example_population_pk.csv
        │
        └── validation/
            ├── __init__.py
            ├── reference_datasets/
            ├── compare_r_outputs.py
            └── unit_tests.py
```

Use the `src/` layout because it helps avoid accidental imports from the local development folder instead of the installed package.

---

## 7. Module 1 — Dissolution Analysis

This should be the first MVP.

### Why start here?

- Directly useful to formulation scientists
- Easier than NLME/popPK
- Commercially relevant
- Clear competitor landscape: Excel, DDSolver, GraphPad, manual R scripts
- Strong report-generation opportunity

### Main features

```python
from openpkflow.dissolution import f1, f2, bootstrap_f2, fit_dissolution_models

f2_value = f2(reference, test, time)
ci = bootstrap_f2(reference_replicates, test_replicates, time, n_boot=5000)
models = fit_dissolution_models(time, percent_released)
```

### Required functions

```text
f1()
f2()
bootstrap_f2()
fit_zero_order()
fit_first_order()
fit_higuchi()
fit_korsmeyer_peppas()
fit_hixson_crowell()
fit_weibull()
profile_plot()
residual_plot()
report_pdf()
report_html()
```

### Dissolution models to include

| Model | Use |
|---|---|
| Zero-order | Constant release |
| First-order | Concentration-dependent release |
| Higuchi | Matrix diffusion |
| Korsmeyer–Peppas | Mechanism screening |
| Hixson–Crowell | Erosion/surface-area change |
| Weibull | Flexible empirical release fitting |

### Expected outputs

```text
- f1 value
- f2 value
- bootstrap f2 confidence interval
- model parameters
- AIC/BIC
- R² / adjusted R²
- residual plots
- dissolution profile plots
- interpretation paragraph
- PDF/HTML report
- Excel summary table
```

### Example input CSV

```csv
formulation,batch,time,percent_released
reference,R1,5,18.2
reference,R1,10,31.4
reference,R1,15,47.9
test,T1,5,17.5
test,T1,10,30.1
test,T1,15,46.2
```

### Example API

```python
from openpkflow.dissolution import DissolutionStudy

study = DissolutionStudy.from_csv("dissolution.csv")

study.compare(
    reference="reference",
    test="test",
    method="bootstrap_f2",
    n_boot=5000,
)

study.fit_models([
    "zero_order",
    "first_order",
    "higuchi",
    "korsmeyer_peppas",
    "weibull",
])

study.report("dissolution_report.pdf")
```

---

## 8. Module 2 — NCA Engine

NCA should be the second MVP.

### Goal

Create a Python workflow inspired by the practical strengths of R's `PKNCA`.

The package should not only calculate PK parameters. It should handle:

- data checks
- AUC method selection
- terminal phase estimation
- individual summaries
- group summaries
- plots
- report-ready tables
- warnings
- reproducibility metadata

### Main API

```python
from openpkflow.nca import NCAStudy

study = NCAStudy.from_csv(
    "pk_data.csv",
    subject_col="subject",
    time_col="time",
    conc_col="concentration",
    dose_col="dose",
)

results = study.run(method="linear_up_log_down")
results.to_excel("nca_results.xlsx")
results.report("nca_report.pdf")
```

### NCA parameters to support

| Parameter | Meaning |
|---|---|
| Cmax | Maximum observed concentration |
| Tmax | Time of Cmax |
| AUC0-t | Area under concentration-time curve to last measurable timepoint |
| AUC0-inf | Extrapolated AUC |
| λz | Terminal elimination rate constant |
| t1/2 | Half-life |
| CL/F | Apparent clearance |
| Vd/F | Apparent volume of distribution |
| MRT | Mean residence time |
| AUMC | Area under first moment curve |

### AUC methods

```text
linear trapezoidal
log trapezoidal
linear-up/log-down
```

### NCA report sections

```text
1. Dataset summary
2. Dosing information
3. Concentration-time plot
4. Individual PK parameter table
5. Mean ± SD summary
6. Terminal phase selection
7. AUC method used
8. Assumptions and warnings
9. Export-ready table
10. Reproducibility metadata
```

---

## 9. Module 3 — PK/PD Simulation

Python has strong numerical tools, but they are generic. OpenPKFlow should make them pharmacometric.

### Main API

```python
from openpkflow.sim import OneCompartmentOral

model = OneCompartmentOral(
    ka=1.2,
    cl=5.0,
    v=50.0,
    f=0.8,
)

sim = model.simulate(
    dose=500,
    times=[0, 0.5, 1, 2, 4, 8, 12, 24],
)

sim.plot()
```

### Models to include

```text
one-compartment IV bolus
one-compartment oral
one-compartment infusion
two-compartment IV
two-compartment oral
repeated dosing
multiple-dose steady-state
simple Emax PD
indirect response model
tumor-growth inhibition model
```

### Key design principle

The user should not need to manually write ODE code for common models.

---

## 10. Module 4 — Population PK Helpers

Do this after dissolution, NCA, and simulation.

Do not attempt to build a full NONMEM replacement in the beginning.

Start with tools that help users prepare and diagnose population PK workflows:

```text
NONMEM dataset preparation
nlmixr2-style dataset preparation
Pharmpy bridge
covariate summaries
missing data checks
concentration-time spaghetti plots
goodness-of-fit plots
VPC-style plots
ETA/covariate plots
```

### Example API

```python
from openpkflow.pop import PopPKDataset

study = PopPKDataset("pop_pk_data.csv")

study.validate_nonmem_format()
study.summary()
study.plot_concentration_time()
study.export_nonmem("nm_ready.csv")
```

---

## 11. Module 5 — Pharmpy Bridge

Pharmpy is already a serious Python pharmacometrics package. OpenPKFlow should complement it.

### Do not duplicate Pharmpy

Avoid rebuilding:

```text
NONMEM parsing
model-code manipulation
advanced model search algorithms
engine execution management
```

### What OpenPKFlow should add

```text
clean user interface
formulation-friendly workflows
reports
plots
validation checks
teaching examples
interpretation helpers
```

### Example API

```python
from openpkflow.pop import load_pharmpy_model

model = load_pharmpy_model("run001.mod")
summary = model.clean_summary()
summary.to_html("model_summary.html")
```

---

## 12. Module 6 — Bayesian PK

This is where Python becomes powerful.

Recommended tools:

```text
PyMC
CmdStanPy
ArviZ
NumPyro, optional later
```

### First Bayesian models

```text
Bayesian one-compartment model
Bayesian two-compartment model
Bayesian NCA uncertainty
Bayesian dissolution model fitting
Bayesian IVIVC exploratory model
```

### Example API

```python
from openpkflow.bayes import BayesianOneCompartment

fit = BayesianOneCompartment(data=df).fit()
fit.posterior_summary()
fit.plot_posterior()
fit.report("bayesian_pk_report.pdf")
```

---

## 13. Module 7 — ML / Deep Learning Layer

This should come after the classical workflow is trusted.

### Possible features

```text
dissolution profile prediction
particle size prediction
formulation feature engineering
Bayesian optimization
neural ODE PK
uncertainty-aware formulation screening
generative formulation suggestion
```

### Do not overhype

Avoid:

> “AI discovers the perfect formulation.”

Use:

> **ML-assisted decision support for formulation and PK workflows where data quality is sufficient.**

---

## 14. Validation Strategy

Validation is the core of trust.

### Layer 1 — Unit tests

Each formula should have tests:

```text
test_f2_known_example()
test_auc_linear()
test_auc_log()
test_half_life()
test_cmax_tmax()
test_weibull_fit()
```

### Layer 2 — Reference examples

Use:

```text
published examples
package vignettes
simulated datasets
manual Excel calculations
R package outputs
```

### Layer 3 — Cross-tool comparison

Compare outputs against:

```text
PKNCA
bootf2
DDSolver
Phoenix/WinNonlin, if available
GraphPad/Excel manual calculations
```

### Layer 4 — Report validation

Every report should include:

```text
input file hash
software version
calculation method
assumptions
warnings
date/time
author/exporter
exported tables
```

### Layer 5 — Regulatory caution

Include this disclaimer:

> This report is generated using open-source computational workflows. Final regulatory interpretation should be reviewed by qualified formulation, pharmacokinetic, and regulatory experts.

---

## 15. Tech Stack

| Need | Recommended tool |
|---|---|
| Data handling | pandas, polars |
| Math | NumPy |
| Curve fitting | SciPy |
| ODE solving | SciPy solve_ivp |
| Plotting | matplotlib, plotly optional |
| Reports | Jinja2 + WeasyPrint or ReportLab |
| Word export | python-docx |
| Excel export | openpyxl |
| Validation | pytest |
| CLI | Typer |
| Config/input validation | Pydantic |
| Bayesian modelling | PyMC, CmdStanPy |
| ML | scikit-learn, PyTorch |
| Neural ODE | torchdiffeq |
| Docs | MkDocs Material |
| Packaging | hatchling or setuptools |
| CI/CD | GitHub Actions |

---

## 16. CLI Design

OpenPKFlow should work from Python and terminal.

### Dissolution CLI

```bash
openpkflow dissolution compare dissolution.csv \
  --reference reference \
  --test test \
  --bootstrap 5000 \
  --report dissolution_report.pdf
```

### NCA CLI

```bash
openpkflow nca run pk_data.csv \
  --subject subject \
  --time time \
  --conc concentration \
  --dose dose \
  --report nca_report.pdf
```

CLI support matters because CROs, consultants, and labs often need repeatable workflows.

---

## 17. Documentation Plan

Recommended documentation structure:

```text
docs/
├── index.md
├── getting-started.md
├── installation.md
├── publishing-to-pypi.md
├── dissolution/
│   ├── f1-f2.md
│   ├── bootstrap-f2.md
│   ├── model-fitting.md
│   └── report-generation.md
├── nca/
│   ├── auc-methods.md
│   ├── lambda-z.md
│   ├── parameter-table.md
│   └── nca-report.md
├── simulation/
│   ├── one-compartment.md
│   ├── two-compartment.md
│   ├── repeated-dosing.md
│   └── infusion.md
├── validation/
│   ├── reference-outputs.md
│   └── comparison-with-r.md
└── api/
```

---

## 18. Report Design

This is where OpenPKFlow can beat Excel/DDSolver-style workflows.

### Report sections

```text
Title
Study metadata
Input data summary
Method used
Data validation checks
Main results
Plots
Model fitting table
Interpretation
Warnings
Exported tables
Software version
Reproducibility note
```

### Example interpretation text

> The calculated f2 value was 67.4, suggesting similarity between the reference and test dissolution profiles under the selected timepoints. Bootstrap analysis produced a 90% confidence interval of 59.2–74.8, supporting the robustness of the similarity conclusion. Interpretation should consider variability, sampling design, and regulatory context.

---

## 19. Competitive Positioning

| Existing tool | Weakness | OpenPKFlow advantage |
|---|---|---|
| Excel | Manual, error-prone, ugly reports | Automated, validated, clean report |
| DDSolver | Useful but dated output | Modern Python package + reports |
| GraphPad | Good plots, not pharma-specific | Pharma-specific interpretation |
| R packages | Powerful but fragmented | Unified Python workflow |
| Certara/Phoenix | Expensive, enterprise-heavy | Lightweight, open, service-friendly |
| Pharmpy | Strong pharmacometric backend | You add formulation/NCA/report UX |

---

## 20. Critical Risks

### Risk 1 — Regulatory overclaiming

Do not say:

> “FDA-approved Python package.”

Say:

> “Transparent, validated, open-source computational workflow.”

### Risk 2 — Trying to build everything

Avoid building NCA + NLME + PBPK + AI at once.

Start with dissolution.

### Risk 3 — Copying R code

You can study R package behavior, formulas, documentation, and outputs, but do not copy code unless the license explicitly allows it.

### Risk 4 — Weak validation

If outputs differ from R/Phoenix/Excel without explanation, users will lose trust.

Validation is not optional.

### Risk 5 — Over-AI branding

Do not make it look like a generic AI startup.

Make it look like serious formulation informatics.

---

## 21. First 10 Development Tasks

```text
1. Create GitHub repo
2. Create package skeleton
3. Implement f1
4. Implement f2
5. Add dissolution CSV parser
6. Add bootstrap f2
7. Add profile plot
8. Add Weibull + Korsmeyer-Peppas fitting
9. Add PDF/HTML report
10. Validate against manual examples and R bootf2-style outputs
```

---

# 22. Publishing OpenPKFlow to PyPI

Goal:

```bash
pip install openpkflow
```

To make this work, the package must be uploaded to PyPI under the project name `openpkflow`.

---

## 22.1 Check package name availability

Package names on PyPI are global. Before finalizing the name, check:

```text
https://pypi.org/project/openpkflow/
```

If PyPI shows **404 Not Found**, the name is likely available. However, availability can change at any time, so register/publish early once you decide.

---

## 22.2 Recommended project layout

Use this minimal layout:

```text
openpkflow/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/
│   └── openpkflow/
│       ├── __init__.py
│       └── dissolution/
│           ├── __init__.py
│           └── similarity.py
└── tests/
    └── test_similarity.py
```

---

## 22.3 Minimal `pyproject.toml`

Use this as your starting file:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "openpkflow"
version = "0.1.0"
description = "Python-first toolkit for dissolution, NCA, PK/PD simulation, and pharmacometric reporting."
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [
  { name = "Priyam T." }
]
keywords = [
  "pharmacokinetics",
  "pharmacometrics",
  "dissolution",
  "NCA",
  "PKPD",
  "formulation",
  "bioequivalence"
]
classifiers = [
  "Development Status :: 2 - Pre-Alpha",
  "Intended Audience :: Science/Research",
  "Intended Audience :: Healthcare Industry",
  "License :: OSI Approved :: MIT License",
  "Programming Language :: Python :: 3",
  "Programming Language :: Python :: 3.10",
  "Programming Language :: Python :: 3.11",
  "Programming Language :: Python :: 3.12",
  "Topic :: Scientific/Engineering",
]
dependencies = [
  "numpy>=1.24",
  "pandas>=2.0",
  "scipy>=1.10",
  "matplotlib>=3.7",
  "pydantic>=2.0",
  "typer>=0.12",
  "jinja2>=3.1",
]

[project.optional-dependencies]
reports = [
  "weasyprint>=61.0",
  "openpyxl>=3.1",
]
bayes = [
  "pymc>=5.0",
  "arviz>=0.16",
  "cmdstanpy>=1.2",
]
ml = [
  "scikit-learn>=1.4",
  "torch>=2.0",
]
dev = [
  "pytest>=8.0",
  "ruff>=0.5",
  "mypy>=1.8",
  "build>=1.2",
  "twine>=5.0",
]

[project.urls]
Homepage = "https://github.com/YOUR_USERNAME/openpkflow"
Repository = "https://github.com/YOUR_USERNAME/openpkflow"
Issues = "https://github.com/YOUR_USERNAME/openpkflow/issues"
Documentation = "https://YOUR_USERNAME.github.io/openpkflow/"

[project.scripts]
openpkflow = "openpkflow.cli:app"
```

---

## 22.4 Minimal package code

Create:

```text
src/openpkflow/__init__.py
```

```python
__version__ = "0.1.0"
```

Create:

```text
src/openpkflow/dissolution/similarity.py
```

```python
from __future__ import annotations

import math
from collections.abc import Sequence


def f2(reference: Sequence[float], test: Sequence[float]) -> float:
    """Calculate similarity factor f2 for two dissolution profiles.

    Parameters
    ----------
    reference:
        Reference product percent release values.
    test:
        Test product percent release values.

    Returns
    -------
    float
        f2 similarity factor.
    """
    if len(reference) != len(test):
        raise ValueError("Reference and test profiles must have the same length.")
    if len(reference) == 0:
        raise ValueError("Profiles must not be empty.")

    n = len(reference)
    squared_diff_sum = sum((r - t) ** 2 for r, t in zip(reference, test))
    return 50 * math.log10((1 + squared_diff_sum / n) ** -0.5 * 100)


def f1(reference: Sequence[float], test: Sequence[float]) -> float:
    """Calculate difference factor f1 for two dissolution profiles."""
    if len(reference) != len(test):
        raise ValueError("Reference and test profiles must have the same length.")
    denominator = sum(reference)
    if denominator == 0:
        raise ValueError("Reference profile sum must not be zero.")
    numerator = sum(abs(r - t) for r, t in zip(reference, test))
    return 100 * numerator / denominator
```

Create:

```text
src/openpkflow/dissolution/__init__.py
```

```python
from .similarity import f1, f2

__all__ = ["f1", "f2"]
```

---

## 22.5 Minimal CLI

Create:

```text
src/openpkflow/cli.py
```

```python
import typer

from openpkflow.dissolution import f1, f2

app = typer.Typer(help="OpenPKFlow command-line interface.")


@app.command()
def version() -> None:
    """Show package version."""
    from openpkflow import __version__

    typer.echo(f"openpkflow {__version__}")


@app.command()
def similarity(
    reference: str = typer.Option(..., help="Comma-separated reference values."),
    test: str = typer.Option(..., help="Comma-separated test values."),
) -> None:
    """Calculate f1 and f2 from comma-separated values."""
    ref_values = [float(x) for x in reference.split(",")]
    test_values = [float(x) for x in test.split(",")]

    typer.echo(f"f1 = {f1(ref_values, test_values):.3f}")
    typer.echo(f"f2 = {f2(ref_values, test_values):.3f}")
```

Test after installation:

```bash
openpkflow version
openpkflow similarity --reference "20,40,60,80" --test "21,39,61,79"
```

---

## 22.6 Add tests

Create:

```text
tests/test_similarity.py
```

```python
import pytest

from openpkflow.dissolution import f1, f2


def test_f2_identical_profiles_is_100():
    assert f2([10, 20, 30], [10, 20, 30]) == pytest.approx(100.0)


def test_f1_identical_profiles_is_zero():
    assert f1([10, 20, 30], [10, 20, 30]) == pytest.approx(0.0)


def test_f2_requires_same_length():
    with pytest.raises(ValueError):
        f2([10, 20], [10, 20, 30])
```

Run:

```bash
pytest
```

---

## 22.7 Build the package locally

Install build tools:

```bash
python -m pip install --upgrade pip build twine
```

Build source distribution and wheel:

```bash
python -m build
```

This creates:

```text
dist/openpkflow-0.1.0.tar.gz
dist/openpkflow-0.1.0-py3-none-any.whl
```

Check the distribution:

```bash
python -m twine check dist/*
```

---

## 22.8 Test on TestPyPI first

Create accounts:

```text
https://test.pypi.org/account/register/
https://pypi.org/account/register/
```

Upload to TestPyPI:

```bash
python -m twine upload --repository testpypi dist/*
```

Install from TestPyPI:

```bash
python -m pip install --index-url https://test.pypi.org/simple/ openpkflow
```

For packages with dependencies, use:

```bash
python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  openpkflow
```

---

## 22.9 Upload to real PyPI manually

Once TestPyPI works:

```bash
python -m twine upload dist/*
```

Then users can install:

```bash
pip install openpkflow
```

Important: PyPI does not allow re-uploading the same version. If something is wrong, increase the version number:

```toml
version = "0.1.1"
```

Then rebuild and upload again:

```bash
rm -rf dist/
python -m build
python -m twine upload dist/*
```

On Windows PowerShell:

```powershell
Remove-Item -Recurse -Force dist
python -m build
python -m twine upload dist/*
```

---

## 22.10 Use API token authentication

For manual upload, do not use your PyPI password.

Use an API token:

1. Go to PyPI account settings
2. Create API token
3. During upload, use:

```text
username: __token__
password: pypi-xxxxxxxxxxxxxxxx
```

Command:

```bash
python -m twine upload -u __token__ -p YOUR_API_TOKEN dist/*
```

Do not commit the token to GitHub.

---

## 22.11 Recommended: Trusted Publishing with GitHub Actions

The safer modern method is PyPI Trusted Publishing.

This avoids long-lived PyPI tokens in GitHub secrets.

### GitHub Actions workflow

Create:

```text
.github/workflows/publish.yml
```

```yaml
name: Publish Python package

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install build tool
        run: python -m pip install --upgrade build

      - name: Build package
        run: python -m build

      - name: Publish package to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

### PyPI setup for Trusted Publishing

On PyPI:

```text
Project name: openpkflow
Owner: YOUR_GITHUB_USERNAME or organization
Repository name: openpkflow
Workflow filename: publish.yml
Environment name: leave blank unless you use GitHub environments
```

Then create a GitHub release. The workflow builds and publishes to PyPI.

---

## 22.12 Versioning strategy

Use semantic versioning:

```text
0.1.0 = first working dissolution MVP
0.2.0 = bootstrap f2 + model fitting
0.3.0 = report generation
0.4.0 = NCA engine
0.5.0 = PK simulation
1.0.0 = stable dissolution + NCA + report API
```

Avoid publishing too many broken versions. PyPI releases are public and hard to clean up.

---

## 22.13 First README for PyPI

Use this README skeleton:

```markdown
# OpenPKFlow

OpenPKFlow is a Python-first toolkit for dissolution similarity, non-compartmental analysis, PK/PD simulation, and regulatory-style pharmacometric reporting.

## Install

```bash
pip install openpkflow
```

## Example

```python
from openpkflow.dissolution import f1, f2

reference = [20, 40, 60, 80]
test = [21, 39, 61, 79]

print(f1(reference, test))
print(f2(reference, test))
```

## Philosophy

OpenPKFlow is designed for transparent, reproducible, and auditable pharmacometric workflows. It does not replace expert regulatory judgement or validated commercial platforms. It helps scientists generate clean calculations, plots, and reports using open-source Python.

## Current modules

- Dissolution f1/f2
- Bootstrap f2, planned
- Dissolution model fitting, planned
- NCA parameter calculation, planned
- PK simulation, planned
- Report generation, planned

## Disclaimer

This software is for research and decision-support workflows. Final regulatory interpretation should be reviewed by qualified formulation, pharmacokinetic, and regulatory experts.
```

---

## 23. Exact Windows PowerShell Commands

From your project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install build twine pytest ruff
pytest
python -m build
python -m twine check dist/*
python -m twine upload --repository testpypi dist/*
```

Then test:

```powershell
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ openpkflow
openpkflow version
```

Final upload:

```powershell
python -m twine upload dist/*
```

Then anyone can run:

```powershell
pip install openpkflow
```

---

## 24. Final Recommendation

Start with this minimal release:

```text
openpkflow 0.1.0
├── f1()
├── f2()
├── CLI command for f1/f2
├── tests
├── README
├── pyproject.toml
└── PyPI upload
```

Then build:

```text
0.2.0 = bootstrap f2
0.3.0 = dissolution model fitting
0.4.0 = report generator
0.5.0 = NCA
0.6.0 = PK simulation
0.7.0 = population PK diagnostics
0.8.0 = Pharmpy bridge
0.9.0 = Bayesian/ML prototypes
1.0.0 = stable public release
```

This gives you a realistic path from idea to public package:

```bash
pip install openpkflow
```

---

## 25. Official References Checked

These sources were used to ground the packaging and PyPI publication steps:

1. Python Packaging User Guide — Packaging Python Projects  
   https://packaging.python.org/tutorials/packaging-projects/

2. Python Packaging User Guide — Writing `pyproject.toml`  
   https://packaging.python.org/en/latest/guides/writing-pyproject-toml/

3. Python Packaging User Guide — src layout vs flat layout  
   https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/

4. PyPI Docs — Trusted Publishers  
   https://docs.pypi.org/trusted-publishers/

5. Python Packaging User Guide — Publishing package distributions using GitHub Actions CI/CD workflows  
   https://packaging.python.org/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/

6. Twine documentation  
   https://twine.readthedocs.io/

7. PyPI Help — API tokens  
   https://pypi.org/help/

8. PyPI project-name check for `openpkflow`  
   https://pypi.org/project/openpkflow/

