# CLAUDE.md -- openfit

This file provides guidance to Claude Code (claude.ai/code) when working with code in the openfit repository.

## Scope and boundary (read this first)

**In scope -- build, extend, polish:**
- `models/` -- built-in equation library (~30+ models: sigmoidal, exponential, Michaelis-Menten, polynomial, growth, decay, Gaussian, Boltzmann)
- `fit.py` -- core Fit engine (weighted nonlinear least squares via scipy least_squares)
- `weighting.py` -- 1/Y, 1/Y^2, 1/SD^2, Poisson, iterative reweighting
- `uncertainty.py` -- asymptotic SE, profile-likelihood CI, bootstrap CI
- `compare.py` -- model comparison: AICc, BIC, F-test (extra sum-of-squares), R^2, adjusted R^2
- `diagnostics.py` -- residual analysis, runs test, replicates test, normality test
- `global_fit.py` -- shared-parameter fitting across multiple datasets (the moat)
- `outliers.py` -- ROUT adaptive outlier detection (Motulsky & Brown, BMC Bioinformatics 2006)
- `spec.py` -- FitSpec: reproducibility manifest (model + data hash + weights + seed + version)
- `report/` -- HTML, PDF (ReportLab), Markdown fit reports with overlay + residual panel
- `io/` -- CSV/Excel loader, Prism XML import (read-only, for migration)
- `validation/` -- NIST StRD certified-value recovery tests

**Out of scope -- do not build:**
- GUI / desktop app / Electron wrapper -- openfit is library-first, CLI-second.
- Bayesian fitting (PyMC/Stan) -- that is a separate package or optional extension. Do not add PyMC as a core dependency.
- Mixed-effects / hierarchical models -- belongs in dedicated NLME tools (nlmixr2, Pharmpy).
- Time-series models (ARIMA, state-space) -- different domain.
- Machine learning / neural network fitting -- not curve fitting.
- Image analysis, plate reader hardware integration, or instrument drivers.
- Domain-specific logic (PK parameters, ELISA back-calculation, dose-response IC50 interpretation) -- that belongs in domain packages like openassayflow or openpkflow that import openfit.

**Rules for AI agents:**
1. Before adding any feature, verify it is on the in-scope list. If not, ask the user.
2. Validation work outranks new features. Do not add a new model when existing models lack NIST StRD cross-validation.
3. openfit is a DOMAIN-AGNOSTIC fitting engine. It knows nothing about pharmacology, biology, or chemistry. Domain interpretation belongs in downstream packages.
4. When ROADMAP.md and CLAUDE.md disagree, CLAUDE.md wins. Flag the conflict to the user.
5. Never use `--no-verify` to bypass pre-commit hooks. Fix the underlying issue instead.

---

## Identity

**Package:** `openfit`
**Author:** Priyam Thakar <priyamthakar1@gmail.com>
**GitHub:** https://github.com/priyamthakar/openfit
**PyPI target:** `pip install openfit`
**License:** MIT
**Philosophy:** Reproducible, transparent, open-source nonlinear curve fitting with publication-quality reports. Every fit emits a spec so anyone can reproduce the exact result. Prism's UX with open-source transparency.

**Relationship to openpkflow:** openfit is a standalone, domain-agnostic package. openpkflow MAY depend on openfit in the future for its model-fitting needs, but openfit NEVER imports openpkflow. No shared code, no shared release cycle. They are sibling projects, not parent-child.

---

## Commands

```bash
# Install in editable mode with dev tools
pip install -e ".[dev]"

# Run all tests
pytest

# Run NIST StRD validation suite only
pytest tests/validation/test_nist_strd.py -v

# Run single module
pytest tests/test_fit.py

# Run with coverage
pytest --cov=src/openfit --cov-report=term-missing

# Lint and auto-fix
ruff check src/ tests/ --fix
ruff format src/ tests/

# Type-check
mypy src/openfit

# Build wheel/sdist
python -m build

# CLI
openfit version
openfit fit data.csv --model hill4 --weights 1/y2 --report out.html
openfit compare data.csv --models hill3,hill4,hill5 --report comparison.html
```

---

## Architecture

- **Layout:** `src/` layout (PEP 517/518). Always import from `src/openfit/`, never from project root.
- **Build:** hatchling (`pyproject.toml`)
- **Python floor:** 3.10+
- **Core deps:** numpy, pandas, scipy, matplotlib, pydantic
- **Optional deps:** `[cli]` (typer, rich), `[reports]` (jinja2, reportlab, python-docx), `[dev]` (pytest, ruff, mypy, build, twine)
- **Avoid WeasyPrint** -- Windows/GTK dependencies are painful. Use ReportLab for PDF.

### Module map

```
openfit/
  models/
    __init__.py      -- ModelRegistry, get_model(), list_models()
    base.py          -- BaseModel protocol: equation, param_names, initial_guess(), bounds()
    sigmoidal.py     -- Hill3P, Hill4P (4PL), Hill5P (5PL), Boltzmann
    exponential.py   -- MonoExp, BiExp, ExpGrowth, ExpPlateau, ExpDecay
    enzyme.py        -- MichaelisMenten, SubstrateInhibition, Allosteric
    growth.py        -- Logistic3P, Logistic4P, Gompertz, Richards
    gaussian.py      -- Gaussian, BiGaussian, Lorentzian
    polynomial.py    -- Poly1..Poly6 (convenience wrappers)
    custom.py        -- CustomModel: user-supplied equation string or callable
  fit.py             -- Fit(model, x, y, ...) -> FitResult
                        wraps scipy.optimize.least_squares (Levenberg-Marquardt + TRF)
                        analytic Jacobian where provided, otherwise finite-diff
  weighting.py       -- WeightScheme enum + apply_weights()
                        1/Y, 1/Y^2, 1/SD^2 (replicate), Poisson, uniform, custom callable
  uncertainty.py     -- asymptotic_se(), profile_likelihood_ci(), bootstrap_ci()
  compare.py         -- compare_models() -> ComparisonResult
                        AICc, BIC, F-test (nested), R^2, adjusted R^2, evidence ratio
  diagnostics.py     -- residual_analysis(), runs_test(), replicates_test(), normality_test()
  global_fit.py      -- GlobalFit(datasets, model, shared=["Top","Bottom"], local=["EC50"])
                        shared-parameter fitting across N datasets (key differentiator)
  outliers.py        -- rout_outliers() -- ROUT adaptive method (Motulsky & Brown 2006)
  spec.py            -- FitSpec dataclass: model_id, param_values, weights, data_hash,
                        openfit_version, scipy_version, numpy_version, random_seed
                        .to_json() / .from_json() for full reproducibility
  results.py         -- FitResult: params, se, ci, r_squared, aic, residuals, spec
                        .summary(), .plot(), .report()
  plotting.py        -- fit_overlay_plot(), residual_plot(), qq_plot() -> base64 PNG
  report/
    __init__.py      -- report_fit(), report_comparison() dispatchers
    templates/       -- Jinja2 HTML templates
    html.py          -- HTML renderer
    markdown.py      -- Markdown renderer
    pdf.py           -- ReportLab PDF renderer
  io/
    __init__.py      -- load_csv(), load_excel()
    loader.py        -- flexible CSV/Excel ingestion with column mapping
    prism_import.py  -- read-only Prism .pzfx XML parser (migration helper)
  cli.py             -- Typer CLI entry point
  validation/        -- NIST StRD reference data + certified values (shipped with package)
```

### Data flow

```
CSV/Excel file or (x, y) arrays
  -> Fit(model, x, y, weights=..., method=...)
       1. initial_guess() from model (smart defaults per model type)
       2. apply_weights() if specified
       3. scipy.optimize.least_squares (LM or TRF)
       4. asymptotic SE from covariance matrix
       5. optional: profile_likelihood_ci() or bootstrap_ci()
       6. GOF: R^2, adjusted R^2, AICc, BIC, runs test
  -> FitResult
       .params          dict of fitted values
       .se              standard errors
       .ci              confidence intervals (asymptotic, profile, or bootstrap)
       .r_squared       coefficient of determination
       .aic / .bic      information criteria
       .residuals       raw + weighted residuals
       .spec            FitSpec (full reproducibility manifest)
  -> result.report("fit.html")   -> publication-quality HTML/PDF/Markdown report
  -> result.spec.to_json()       -> reproducibility manifest (JSON)
```

### Global fit data flow

```
Multiple (x, y) datasets
  -> GlobalFit(datasets, model, shared=["Top","Bottom"], local=["EC50","HillSlope"])
       1. stack datasets with dataset index
       2. shared params: single value across all datasets
       3. local params: independent value per dataset
       4. joint least_squares optimization
       5. F-test: is sharing justified? (extra sum-of-squares)
  -> GlobalFitResult
       .shared_params   dict of shared parameter values
       .local_params    list of dicts per dataset
       .f_test          comparison: shared vs independent fits
```

---

## Correctness Rules (load-bearing)

These are non-negotiable. Do not violate them.

1. **Weighting must be explicit.** Never silently default to uniform weights. The Fit() constructor requires `weights=` or `weights="uniform"`. Implicit unweighted 4PL on heteroscedastic data (e.g., ELISA) is a common source of wrong results.

2. **Initial guesses must be smart, not random.** Each model provides an `initial_guess(x, y)` method that uses data-driven heuristics (e.g., min/max for Top/Bottom, midpoint for EC50). Random starts are for Monte Carlo exploration, not default behavior.

3. **Profile-likelihood CI must warn when the profile is not unimodal.** If the likelihood profile has multiple local minima or the boundary is hit, flag it -- do not silently return a garbage interval.

4. **F-test for nested models only.** The extra sum-of-squares F-test is only valid when one model is a special case of the other (e.g., Hill3P is nested in Hill4P). compare_models() must check nestedness before computing F-test p-values. For non-nested models, use AICc only.

5. **FitSpec must be deterministic.** Given the same spec, the same result must be produced. This means: fixed random_seed for bootstrap, pinned scipy/numpy versions in the spec, and data identified by SHA-256 hash.

6. **NIST StRD certified values must be recovered.** For each NIST nonlinear dataset, fitted parameters must match certified values within the dataset's stated precision. This is the acceptance criterion -- if a code change breaks NIST recovery, the change is rejected.

7. **Residuals must be accessible.** Every FitResult exposes raw residuals, weighted residuals, and standardized residuals. No black boxes.

8. **NaN/Inf in input data must raise ValueError.** Do not silently drop or interpolate. The user must clean their data explicitly.

9. **R^2 for nonlinear fits must use the correct definition.** R^2 = 1 - SS_res/SS_tot, where SS_tot uses the mean of y. Do NOT use the "generalized R^2" or pseudo-R^2 without labeling it. For weighted fits, use weighted SS.

10. **Disclaimer in all generated reports:**
    > This report was generated using openfit (open-source). Results should be independently verified for regulatory or clinical decision-making.

---

## Validation Discipline (mandatory from day one)

### NIST StRD Nonlinear Regression

The NIST Statistical Reference Datasets (https://www.itl.nist.gov/div898/strd/nls/nls_main.shtml) provide certified parameter values for 27 nonlinear regression problems at three difficulty levels.

**Must-pass datasets (minimum viable validation):**

| Dataset | Model | Params | Difficulty | Why it matters |
|---------|-------|--------|------------|----------------|
| Misra1a | 2-param exponential | 2 | Lower | Basic convergence |
| Chwirut2 | 3-param exponential | 3 | Lower | Weighted regression baseline |
| Gauss1 | 8-param triple Gaussian | 8 | Lower | Multi-peak separation |
| DanWood | 2-param power | 2 | Average | Nonlinear transform |
| Hahn1 | 7-param rational | 7 | Average | Complex rational model |
| Rat42 | 3-param growth | 3 | Average | Growth curve (our bread and butter) |
| MGH17 | 5-param sum of exponentials | 5 | Higher | Notoriously ill-conditioned |
| BoxBOD | 2-param exponential | 2 | Higher | Sensitive to initial values |
| Thurber | 7-param rational | 7 | Higher | The hardest standard test |
| Bennett5 | 3-param exp | 3 | Higher | Near-singular Jacobian |
| Eckerle4 | 3-param Gaussian | 3 | Higher | Extremely narrow peak |

**Acceptance criterion:** Fitted parameters match NIST certified values to at least 6 significant digits (NIST provides 11). Residual sum of squares matches to 6 digits.

**Test structure:**
```
tests/validation/
  test_nist_strd.py          -- parametrized test over all 27 datasets
  nist_data/                 -- raw .dat files from NIST (public domain)
  nist_certified_values.py   -- parsed certified params + SEs + RSS
```

### Cross-validation against R packages

For sigmoidal models (4PL/5PL), cross-validate against:
- R `drc` package (Ritz et al., 2015, PLOS ONE) -- the standard for dose-response
- R `nplr` package (Commo & Bot, 2015) -- n-parameter logistic regression

Study behavior and reference outputs only. Do not copy R source code.

### Every model test must cite its source

Same discipline as openpkflow:
1. A **degenerate/sanity case** with a hand-checkable answer
2. A **published reference** with citation (NIST dataset ID, paper DOI, or textbook equation number)

"I calculated it manually" is not a citation.

---

## Competitive Positioning

### What Prism does that open-source tools lack (our gap targets)

| Feature | Prism | scipy curve_fit | lmfit | openfit target |
|---------|-------|-----------------|-------|----------------|
| Smart initial guesses | Yes (per model) | No | Partial | Yes (per model) |
| 1/Y, 1/Y^2 weighting | Yes (menu) | Manual | Manual | Yes (enum) |
| Global/shared fitting | Yes (core feature) | No | No | Yes (v0.4.0) |
| Profile-likelihood CI | Yes | No | Yes (partial) | Yes (v0.3.0) |
| ROUT outlier removal | Yes (exclusive) | No | No | Yes (v0.5.0) |
| Model comparison F-test | Yes | No | No | Yes (v0.2.0) |
| Reproducibility spec | No (!) | No | No | Yes (v0.1.0) -- our unique moat |
| Publication-quality report | Yes (graph export) | No | No | Yes (v0.1.0) |
| NIST-certified validation | Not published | N/A | Not published | Yes (v0.1.1) |

### What we do NOT compete with

- **lmfit** -- excellent minimization wrapper with constraints and parameter expressions. We use scipy directly but could optionally wrap lmfit. lmfit is a fitting ENGINE; we are a fitting PRODUCT (engine + validation + reports + reproducibility).
- **scipy.optimize** -- the backend we use. We add value on top.
- **statsmodels** -- statistical modeling, not curve fitting. Different audience.

---

## Code Conventions

- **Type hints required** on all public API functions and methods.
- **Docstrings required** on all public functions -- NumPy docstring style.
- **No comments** unless the WHY is non-obvious.
- **No multi-paragraph docstrings** -- one short description, then Parameters/Returns/Raises.
- Line length: 100 characters (ruff).
- Formatting: ruff (`ruff format`), linting: ruff lint, type-checking: mypy strict.

---

## Windows Console Constraint

All CLI output and docstrings must use ASCII-only characters. Unicode punctuation (em dashes, arrows, fancy quotes) causes `UnicodeEncodeError` on Windows cp1252 consoles. Use plain ASCII equivalents.

---

## Git Conventions

- Never force-push. Never `--no-verify`. Never amend published commits.
- Commit message format: `<type>(<scope>): <short description>`
  (e.g., `feat(models): add Hill 4PL with smart initial guesses`)
- Version bumps: update `pyproject.toml` version and `CHANGELOG.md` together in one commit.
- Tag releases: `git tag v0.1.0`

---

## Positioning Reminder

Use:
> **Reproducible, open-source nonlinear curve fitting with publication-quality reports. Every fit you can rerun, every result you can cite.**

Never say:
> "Replaces Prism", "better than Prism", "AI-powered fitting."
