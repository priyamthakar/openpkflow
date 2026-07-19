# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Scope and boundary (read this first)

**In scope — build, extend, polish:**
- `dissolution/` — f1, f2, MSD, model fitting, multi-media, SUPAC screening, alcohol f2
- `nca/` — sparse, steady-state, urinary, CDISC PP (greenfield moat)
- `ivivc/` — Level A + Level B/C helpers (MDT/MRT correlation)
- `sim/` — analytical compartment models, transit oral, SS metrics
- `pipeline/` — multi-stage study orchestration + unified reports (v2.6.0)
- `bayes/` — MAP individual PK (scipy, screening tool, not regulatory primary)
- `be/` — paired TOST convenience layer, formal complete balanced 2x2 crossover
  ANOVA, power/n, and FDA partial-replicate RSABE only after external validation
- `report/` — HTML, PDF, DOCX, Markdown
- `validation/` — cross-checks against published references

**Web app layer (ratified 2026-05-31 — see PIVOT_PLAN.md Option A):**
- `api/` — FastAPI REST adapter. Wraps `openpkflow` public APIs. No pharmacometric math.
  Current routers: nca (including sparse), dissolution (including multi-media), sim,
  ivivc, be (including power/sample size), and pipeline.
- `webapp/` — React + Vite + Tailwind frontend.
  Current pages: Home, NCA, Sparse NCA, Dissolution (single + multi-media tab),
  Simulation, IVIVC, Bioequivalence (analysis + power tab), and Study Pipeline.
- Both dirs are separate from `src/openpkflow/` and do NOT reimplement pharmacometric math.
- Do not add new pharmacometric logic to `api/` or `webapp/`. If a new analysis is needed,
  first add it to the appropriate `src/openpkflow/` module, then expose it in `api/`.
- See `progress_web_app.md` for the full file map, completed features, and next candidates.
- Takeover state: read `HANDOFF.md` first (release state, active branch, resume checklist).

**Out of scope — do not extend (existing code is frozen at v2.3.0):**
- `pop/estimation/` — FOCE-I and SAEM exist but must not be extended. Pharmpy and
  nlmixr2 are validated NLME engines. Bug fixes only. No IOV, no 3-cmt, no covariate
  selection, no iv_infusion route for estimation.
- EMA ABEL, full-replicate RSABE, and formal BE without independent validation fixtures
  are out of scope. FDA partial-replicate RSABE must fail closed as NOT_EVALUABLE until
  its external validation gate is satisfied.
- WeasyPrint, Streamlit/Gradio GUI (as embedded GUI in the library), CDISC Define.xml, eCTD table formatting.
  Note: The `api/` + `webapp/` web application is a separate layer, not a Streamlit/Gradio embed.

**Rules for AI agents:**
1. Before adding any feature, verify it is on the in-scope list. If not, ask the user.
2. Validation work outranks new features. Do not add a new module when existing
   modules lack NONMEM/PKNCA cross-validation.
3. The former covariate API in `pop/estimation/` (`CovariateModel`, `apply_covariates`)
   was a non-functional v2.2.0 skeleton and was removed in v2.3.0. Do not reintroduce
   covariate estimation without a full external validation plan.
4. When ROADMAP.md and CLAUDE.md disagree, CLAUDE.md wins. Flag the conflict to the user.
5. Never use `--no-verify` to bypass pre-commit hooks. Fix the underlying issue instead.

---

## Identity

**Package:** `openpkflow`
**Author:** Priyam Thakar <priyamthakar1@gmail.com>
**GitHub:** https://github.com/priyamthakar/openpkflow
**PyPI target:** `pip install openpkflow`
**License:** MIT
**Philosophy:** Transparent, reproducible, open-source Python workflow for dissolution, NCA, PK/PD simulation, and pharmacometric reporting. Does not replace expert regulatory judgement or validated commercial platforms.

---

## Commands

```bash
# Install in editable mode with dev tools
pip install -e ".[dev]"

# Run all tests (exclude slow MCMC tests)
pytest --ignore=tests/pop/test_saem.py --ignore=tests/bayes/test_bayes_be.py -k "not MCMC and not mcmc"

# Run NCA + validation tests (fast, complete coverage)
pytest tests/nca/ tests/validation/

# Run single module
pytest tests/nca/test_methods.py

# Run with coverage
pytest --cov=src/openpkflow --cov-report=term-missing

# Lint and auto-fix
ruff check src/ tests/ --fix
ruff format src/ tests/

# Type-check
mypy src/openpkflow

# Build wheel/sdist
python -m build

# PKNCA cross-validation (requires R + PKNCA)
"C:\Program Files\R\R-4.6.0\bin\Rscript.exe" -e ".libPaths('D:/R-library/4.6'); source('scripts/pknca_theoph_crossval.R')"

# CLI
openpkflow version
openpkflow similarity --reference "20,40,60,80" --test "21,39,61,79"
openpkflow dissolution compare data.csv --reference reference --test test --report out.html
```

---

## Architecture

- **Layout:** `src/` layout (PEP 517/518). Always import from `src/openpkflow/`, never from project root.
- **Build:** hatchling (`pyproject.toml`)
- **Python floor:** 3.10+
- **Core deps:** numpy, pandas, scipy, matplotlib, pydantic, typer, jinja2
- **Optional deps:** `[reports]` (openpyxl, reportlab, python-docx), `[bayes]` (pymc, arviz, cmdstanpy), `[ml]` (scikit-learn, torch), `[dev]` (pytest, ruff, mypy, build, twine)
- **Avoid WeasyPrint** — Windows/GTK dependencies are painful. Use ReportLab for PDF.

### Module map

```
dissolution/   -- f1, f2, bootstrap, MSD, models, multi_media, supac       DONE (+ v2.6)
nca/           -- AUC, lambda_z, SS, urine, sparse, CDISC PP               DONE
ivivc/         -- Level A WN/LR/convolution/Levy + Level B/C helpers       DONE (+ v2.6)
sim/           -- 1/2-cmt, dosing, transit oral, SS metrics                DONE (+ v2.6)
pipeline/      -- StudyPipeline multi-stage orchestration + reports        DONE v2.6.0
pop/           -- GOF/VPC + estimation/ FROZEN (bug fixes only)            DONE
bayes/         -- MAP + optional PyMC                                      DONE
ml/            -- PKSurrogate (torch MLP, EXPERIMENTAL)                    DONE
report/        -- Markdown, HTML, PDF (ReportLab), Word (python-docx)      DONE
datasets/      -- example CSVs (dissolution + theoph NCA reference)
validation/    -- reference comparison utilities
student/       -- simplified teaching APIs                                 DONE v2.5
cli.py         -- Typer: dissolution, be, ivivc, pop, study run
```

### NCA module layout

```
nca/
  __init__.py      — exports all public symbols
  methods.py       — pure math: auc_linear, auc_log, auc_linear_up_log_down,
                     cmax, tmax, lambda_z (BAR² auto + manual), auc_inf_obs,
                     auc_percent_extrapolated, clearance_volume_parameters
                     _validate_time_conc rejects NaN/Inf, negative conc
  loader.py        — load_nca_csv(): CSV load + BLQ handling
  results.py       — NCAResult (per-subject), NCASummaryResults dataclasses
  study.py         — NCAStudy: from_csv(), analyze() -> NCASummaryResults
                     tlast trimming: strips trailing conc <= 0 before AUClast
  reporting.py     — report_nca_single(), report_nca_summary() (HTML + Markdown)
```

### NCA data flow

```
CSV file
  -> load_nca_csv()            BLQ-handled DataFrame (subject, time, conc, dose, route)
  -> NCAStudy(df, auc_method, blq_method)
  -> study.analyze()           per-subject loop:
                               1. tlast trimming: strip trailing conc <= 0 (FDA/EMA)
                               2. AUClast via chosen method (linear/log/linear_up_log_down)
                               3. Cmax, Tmax from full profile
                               4. lambda_z BAR² auto (post-Cmax positive points)
                               5. AUCinf = AUClast + Clast/lambda_z
                               6. CL_F/Vz_F (oral) or CL/Vz (IV)
  -> NCASummaryResults         list of NCAResult
  -> summary.to_dataframe()    pandas DataFrame
  -> summary.report("out.html")  -> report_nca_summary() -> nca_summary_report.html
  -> result.report("sub.html")   -> report_nca_single()  -> nca_single_report.html
```

### Sim module layout

```
sim/
  __init__.py    — exports all public symbols
  methods.py     — pure math: c_1cmt_iv_bolus, c_1cmt_iv_infusion, c_1cmt_oral,
                   c_2cmt_iv_bolus, c_2cmt_oral, superpose
  dosing.py      — Dose, DoseRegimen dataclasses; DoseRegimen.from_repeated()
  models.py      — OneCompartmentModel, TwoCompartmentModel (CL/V parameterization)
  simulate.py    — simulate(model, regimen, times) -> SimulationResult
  results.py     — SimulationResult: times, concs, model, regimen, .summary(), .plot(), .report()
  plotting.py    — pk_profile_plot_b64() base64 PNG helper
  reporting.py   — report_simulation() dispatcher (HTML + Markdown + PDF + DOCX)
```

### Sim data flow

```
OneCompartmentModel(route, CL, Vz) or TwoCompartmentModel(...)
  + DoseRegimen.from_repeated(amount, route, tau, n_doses)
  + times array
  -> simulate()         per-dose analytical superposition (linear systems only)
  -> SimulationResult   .times, .concs, .Cmax, .Tmax
  -> result.report("sim.html")   -> report_simulation() -> sim_report.html
```

### Dissolution data flow

```
CSV file
  → load_dissolution_csv()           # pydantic-validated DataFrame
  → DissolutionStudy.from_csv()      # groups by formulation label
  → study.compare(ref, test)         # calls get_formulation_means(), then f1/f2
  → ComparisonResult                 # dataclass: f1_value, f2_value, means, time_points
  → result.summary()                 # text to stdout
  → result.report("out.html")        # → report_dissolution() → render_html_report()
```

### Report rendering

- HTML template lives at `src/openpkflow/report/templates/dissolution_report.html`
- Jinja2 renderer is `src/openpkflow/report/html.py` — note: `zip` is manually injected into `env.globals` because Jinja2 does not expose Python builtins
- Markdown renderer is `src/openpkflow/dissolution/reporting.py`
- Format is inferred from file extension in `report_dissolution()`

### Windows console constraint

All CLI output and docstrings must use ASCII-only characters. Unicode punctuation (em dashes `—`, right arrows `→`, `>=`, `<=`) causes `UnicodeEncodeError` on Windows cp1252 consoles. Use plain ASCII equivalents (`>=`, `->`, `-`).

---

## Validation & Cross-Validation

### PKNCA NCA cross-validation

The NCA module is cross-validated against PKNCA 0.12.1 (Denney et al., 2015) on the
12-subject R nlme::Theoph theophylline dataset. AUClast matches within 2% relative
tolerance for every subject. Cmax matches exactly.

Run with:
```bash
"C:\Program Files\R\R-4.6.0\bin\Rscript.exe" -e ".libPaths('D:/R-library/4.6'); source('scripts/pknca_theoph_crossval.R')"
```

The R script outputs a `_PKNCA_REFERENCE` dict that goes into
`tests/validation/test_nca_theoph_reference.py`.

### Validation test suite

- `tests/validation/test_nca_theoph_reference.py` — per-subject PKNCA cross-validation
- `tests/validation/test_nca_validation.py` — analytical truth recovery (IV bolus, oral)
- `tests/validation/test_sim_validation.py` — Gibaldi & Perrier analytical solutions
- `tests/nca/test_methods.py` — edge cases: all-zero, NaN/Inf, trailing zeros, mixed zeros

Each test cites a source: paper DOI, FDA guidance ID, or reference implementation.

### Known edge cases tested

- All-zero concentrations → AUClast = 0 (no crash)
- NaN/Inf concentrations → ValueError (not silently propagated)
- Trailing zero concentrations → trimmed by tlast logic in study.py
- Single-point profiles → ValueError (need >= 2 for AUC)
- Empty arrays → ValueError
- Negative concentrations → ValueError
- Non-increasing times → ValueError

---

## Current focus

**v2.6.0** is the latest published release (2026-07-15). It includes the study
pipeline, SUPAC/alcohol helpers, IVIVC B/C, transit simulation, web polish, and
convolution validation.

**Immediate next work (in order):**
1. PR #31 (sparse NCA) merged to `main` as squash commit `74c070b` on 2026-07-16.
2. Formal BE ANOVA, RSABE gate, MAP PK hardening, and SUPAC/alcohol hardening are
   open as PR #32 against `main`, CI running.
3. Await conda-forge maintainer review of staged-recipes PR #33461; the v2.6.0
   recipe and all platform builds are green.
4. Find public partial-replicate BE datasets with subject-level data and a
   published FDA RSABE decision to validate `be/rsabe.py`; only then promote it
   from `NOT_EVALUABLE`.
5. Deploy the API/static webapp once the above PR is merged.
6. Keep validation discipline; do not extend frozen `pop/estimation/`.

See `HANDOFF.md` for branch/PR state and `ROADMAP.md` for the full ladder.

**Before any new feature:** run `python -m build && python -m twine check dist/*` to confirm the wheel is clean.

---

## Release Ladder

```
0.1.0 - 1.0.0  core dissolution, NCA, sim, reports, stable release              DONE
1.1.0 - 1.5.0  MSD, IVIVC Level A, SS/urine NCA, multi-media, sparse NCA        DONE
2.0.0          Bayesian MAP + PyMC BE                                           DONE
2.1.0 - 2.3.0  FOCE-I/SAEM, 2-cmt Omega, freeze pop estimation + nlme val       DONE
2.4.0          replicate BE screening + release credibility sprint              DONE
2.5.0          web app (api/ + webapp/) + student helpers                       DONE
2.6.0          study pipeline, SUPAC/alcohol, IVIVC B/C, transit, web polish    RELEASED
0.7.0          Pharmpy bridge                                                   SKIPPED (reserved)
```

See `ROADMAP.md` for full milestone detail, scope rationale, and definition of done.

---

## Code Conventions

- **Type hints required** on all public API functions and methods.
- **Docstrings required** on all public functions — use NumPy docstring style.
- **No comments** unless the WHY is non-obvious (hidden constraint, subtle invariant, workaround).
- **No multi-paragraph docstrings** — one short description line, then Parameters/Returns/Raises sections only.
- Line length: 100 characters (ruff).
- Formatting: ruff (`ruff format`), linting: ruff lint, type-checking: mypy strict.

---

## Pharmacometric Correctness Rules

These are load-bearing. Do not violate them.

1. **f1/f2 require matched time points.** Caller supplies aligned `reference` and `test` arrays. The functions do not silently reindex or interpolate. If arrays differ in length, raise `ValueError`.

2. **AUC method must be explicit.** Never silently default. Always require the caller to pass the method name (`"linear"`, `"log"`, `"linear_up_log_down"`).

3. **Apparent vs absolute parameters must be distinguished in output names.** Use `CL_F` for oral apparent clearance, `CL` for IV-derived clearance. Never mix them in the same output without labelling.

4. **BLQ handling must be explicit.** Never silently drop BLQ values. Require the caller to specify the method.

5. **AUClast stops at tlast.** Following FDA/EMA NCA guidance, AUClast integrates from time 0 to tlast — the last time point with a quantifiable (positive) concentration. Trailing zero or negative concentrations must be excluded from the trapezoidal sum. This is enforced in `study.py`.

6. **NaN/Inf must be rejected.** `_validate_time_conc()` in `methods.py` rejects non-finite concentrations and times with explicit `ValueError` messages. Do not allow NaN to propagate silently through AUC calculations.

7. **Disclaimer required in all generated reports:**
   > This report was generated using OpenPKFlow (open-source). Final regulatory interpretation should be reviewed by qualified formulation, pharmacokinetic, and regulatory experts.

8. **Do not copy code from R packages.** You may study R package behavior, formulas, documentation, and reference outputs. Do not copy source code unless the license explicitly allows it.

---

## Validation Discipline (mandatory from day one)

Every formula function must have at minimum two test cases:

1. A **degenerate/sanity case** with a hand-checkable answer (e.g., identical input → f2 = 100).
2. A **published reference example** with the citation in the test's docstring (paper DOI, FDA guidance ID, or R-package vignette name).

Tests must cite the source of the expected value. "I calculated it manually" is not a citation.

Known reference values:
- f2 = 100 when reference == test (by definition)
- f2 ≈ 50 when profiles differ by ~10 percentage points at each timepoint (FDA 1997 guidance threshold)
- f1 = 0 when reference == test (by definition)
- AUClast matches PKNCA 0.12.1 within 2% on all 12 theophylline subjects
- Cmax matches PKNCA 0.12.1 exactly

---

## Report Format Priority

```
v0.1.x: console summary → Markdown report → HTML report with embedded profile plot
v0.2.x: dissolution model fitting results in reports
v0.3.0: ReportLab PDF export, python-docx Word export
```

OpenPKFlow is **report-first**: the product delivers clean, professional, regulatory-style reports. Calculation correctness is necessary but not sufficient — the output must be shareable with supervisors, clients, CROs, and regulatory teams.

---

## Git Conventions

- Never force-push. Never `--no-verify`. Never amend published commits.
- Commit message format: `<type>(<scope>): <short description>` (e.g., `feat(dissolution): add f1 and f2 with validation`)
- Version bumps: update `pyproject.toml` version and `CHANGELOG.md` together in one commit.
- Tag releases: `git tag v0.1.1`

## PyPI Upload Order

1. tests passing locally
2. `pip install -e .` works
3. `python -m build` succeeds
4. `python -m twine check dist/*` clean
5. Upload to TestPyPI: `twine upload --repository testpypi dist/*`
6. Fresh venv install: `pip install -i https://test.pypi.org/simple/ openpkflow` — verify `openpkflow version` and `openpkflow similarity` work
7. Upload to real PyPI: `twine upload dist/*`

**Preferred: PyPI Trusted Publishing** — no stored token, scoped to the repo. Set up at pypi.org/manage/account/publishing/ then add a `publish.yml` GitHub Actions workflow that triggers on version tags. Only the repo owner can configure this — it requires a one-time manual step at pypi.org.

Do not upload broken or untested wheels.

---

## Positioning Reminder

Use:
> **A transparent, reproducible, open-source Python workflow for dissolution, NCA, PK/PD simulation, and pharmacometric reporting.**

Never say:
> "FDA-approved", "replaces Certara", "AI discovers the perfect formulation."
