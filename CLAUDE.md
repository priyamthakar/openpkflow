# OpenPKFlow — Project Guide for Claude Code

## Identity

**Package:** `openpkflow`  
**Author:** Priyam Thakar <priyamthakar1@gmail.com>  
**GitHub:** https://github.com/priyamthakar1/openpkflow  
**PyPI target:** `pip install openpkflow`  
**License:** MIT  
**Philosophy:** Transparent, reproducible, open-source Python workflow for dissolution, NCA, PK/PD simulation, and pharmacometric reporting. Does not replace expert regulatory judgement or validated commercial platforms.

Full project brief: see `openpkflow_ultimate_project_handout.md` in the repo root.  
PK/PD reference: see `PK_PD_Computational_Modeling_Reference.pdf` in the repo root.

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
dissolution/   — f1, f2, bootstrap_f2, model fitting, loader, reporting   ← current MVP
nca/           — AUC, lambda_z, PK parameters, tables, reporting           ← v0.4.0
sim/           — ODE compartment models, dosing, population sim            ← v0.5.0
pop/           — population PK dataset helpers, diagnostics, VPC           ← v0.6.0
bayes/         — PyMC/Stan Bayesian PK models                              ← v0.8.0
ml/            — neural ODE, features, predictors                          ← v0.9.0
report/        — Markdown, HTML, PDF (ReportLab), Word (python-docx)       ← v0.3.0
datasets/      — example CSV files for tests and examples
validation/    — reference comparison utilities
cli.py         — Typer CLI entry point
```

---

## Release Ladder

```
0.1.0  f1, f2, input validation, CSV loader, CLI, Markdown+HTML report stub, tests
0.1.1  bootstrap_f2 (if clean with tests)
0.2.0  dissolution model fitting (Weibull, Korsmeyer-Peppas, Higuchi, etc.)
0.3.0  full Markdown + HTML + ReportLab PDF report generator
0.4.0  NCA engine (AUC, Cmax, Tmax, lambda_z, t1/2, CL/F, Vz/F)
0.5.0  PK simulation (1-comp, 2-comp, oral, IV, infusion, repeated dosing)
0.6.0  population PK diagnostics, GOF plots, VPC helpers
0.7.0  Pharmpy bridge
0.8.0  Bayesian PK (PyMC, CmdStanPy)
0.9.0  ML / neural ODE prototypes
1.0.0  stable public release
```

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

5. **Disclaimer required in all generated reports:**
   > This report was generated using OpenPKFlow (open-source). Final regulatory interpretation should be reviewed by qualified formulation, pharmacokinetic, and regulatory experts.

6. **Do not copy code from R packages.** You may study R package behavior, formulas, documentation, and reference outputs. Do not copy source code unless the license explicitly allows it.

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

---

## Report Format Priority

```
v0.1.x: console summary → Markdown report → simple HTML report
v0.2.x: dissolution model fitting results in reports
v0.3.0: ReportLab PDF export, python-docx Word export
```

OpenPKFlow is **report-first**: the product delivers clean, professional, regulatory-style reports. Calculation correctness is necessary but not sufficient — the output must be shareable with supervisors, clients, CROs, and regulatory teams.

---

## Git Conventions

- Never force-push. Never `--no-verify`. Never amend published commits.
- Commit message format: `<type>(<scope>): <short description>` (e.g., `feat(dissolution): add f1 and f2 with validation`)
- Version bumps: update `pyproject.toml` version and `CHANGELOG.md` together in one commit.
- Tag releases: `git tag v0.1.0`

## PyPI Upload Order

1. tests passing locally
2. `pip install -e .` works
3. `python -m build` succeeds
4. `python -m twine check dist/*` clean
5. Upload to TestPyPI, install, verify CLI works
6. Upload to real PyPI

Do not upload broken or untested wheels.

---

## Positioning Reminder

Use:
> **A transparent, reproducible, open-source Python workflow for dissolution, NCA, PK/PD simulation, and pharmacometric reporting.**

Never say:
> "FDA-approved", "replaces Certara", "AI discovers the perfect formulation."
