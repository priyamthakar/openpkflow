# OpenPKFlow — Session Context Handout

Read this at the start of every new session. It contains the full current state of the project, design decisions made, known gotchas, and what comes next. Cross-reference with `CLAUDE.md` for code conventions and pharmacometric rules.

---

## Identity

- **Package:** `openpkflow`
- **Author:** Priyam Thakar, priyamthakar1@gmail.com
- **GitHub:** https://github.com/priyamthakar/openpkflow (username: `priyamthakar`, not `priyamthakar1`)
- **PyPI:** https://pypi.org/project/openpkflow/ — live and installable
- **Working directory:** `D:\openpkflow`
- **Python floor:** 3.10+
- **Build:** hatchling, `src/` layout

---

## Current version: 0.1.4

Published to PyPI. GitHub Actions Trusted Publishing handles every release automatically on `v*.*.*` tags.

### Version history

| Version | What shipped |
|---|---|
| 0.1.0 | f1, f2, CSV loader, DissolutionStudy, CLI, Markdown/HTML reports, 50 tests |
| 0.1.1 | bootstrap_f2, profile plot in HTML, CI workflow, example datasets, py.typed |
| 0.1.2 | PyPI Trusted Publishing workflow (no code changes) |
| 0.1.3 | f2(method="regulatory"), CV% warning in compare(), README polish |
| 0.1.4 | DissolutionStudy.bootstrap_compare(), ComparisonResult.plot(), demo.ipynb rewritten |

---

## What is actually built (v0.1.4)

### Public API — entry points users should use

```python
from openpkflow.dissolution import f1, f2, DissolutionStudy, bootstrap_f2, BootstrapF2Result
from openpkflow.datasets import example_dissolution_path, example_similar_path, example_not_similar_path
```

### `f1(reference, test)` / `f2(reference, test, *, method="all_points")`

Scalar functions. Take `Sequence[float]` (plain Python lists), return float.

`f2` accepts `method="all_points"` (default, backwards compatible) or `method="regulatory"` which trims timepoints so at most one has both profiles > 85%, raises `ValueError` if fewer than 3 remain.

Validation: same length, >= 3 points, finite, values in [0, 100].

### `DissolutionStudy`

High-level study object. Always use this when working with CSV data.

```python
study = DissolutionStudy.from_csv("data.csv")
study.formulations()                          # -> list[str]
result = study.compare("reference", "test")   # -> ComparisonResult
boot   = study.bootstrap_compare("reference", "test", n_replicates=5000, seed=42)  # -> BootstrapF2Result
```

`compare()` automatically:
- Warns if more than one timepoint > 85% per FDA guidance
- Warns if CV exceeds FDA limits: > 20% at t <= 15 min, > 10% after

### `ComparisonResult`

Dataclass with: `f1_value`, `f2_value`, `n_timepoints`, `reference_mean`, `test_mean`, `time_points`, `reference_label`, `test_label`.

```python
result.summary()                          # -> str, prints to console
result.report("out.html")                 # -> str, saves HTML (default)
result.report("out.md", format="markdown") # -> str, saves Markdown
result.plot(output_path="plot.png", show=False)  # saves PNG, no matplotlib import needed
result.to_dict()                          # -> dict[str, object]
```

### `bootstrap_f2(reference, test, *, n_replicates, confidence_level, seed)` (low-level)

Takes 2D numpy arrays (n_vessels x n_timepoints). Returns `BootstrapF2Result`.

**Do not expose this in the demo or user docs** — users should call `study.bootstrap_compare()` instead.

### `BootstrapF2Result`

Frozen dataclass: `f2_observed`, `ci_lower`, `ci_upper`, `n_replicates`, `confidence_level`, `n_timepoints`, `n_reference_vessels`, `n_test_vessels`, `is_similar` (property: `ci_lower >= 50`).

```python
boot.summary()  # -> str
boot.is_similar  # -> bool
```

### Datasets

```python
from openpkflow.datasets import example_dissolution_path, example_similar_path, example_not_similar_path
```

All three return str paths to bundled CSV files. Use `importlib.resources` internally.

| Dataset | f2 | Description |
|---|---|---|
| `example_dissolution.csv` | ~58 | Borderline similar |
| `example_similar.csv` | ~80 | Clearly similar |
| `example_not_similar.csv` | ~38 | Clearly not similar |

CSV format: `formulation,batch,time,percent_released` — one row per vessel per timepoint.

---

## Architecture: file map

```
src/openpkflow/
  __init__.py                    # version only
  cli.py                         # Typer CLI: version, similarity, dissolution compare
  py.typed                       # PEP 561 marker

  dissolution/
    __init__.py                  # exports: f1, f2, DissolutionStudy, ComparisonResult,
                                 #          bootstrap_f2, BootstrapF2Result,
                                 #          DissolutionCSVConfig, load_dissolution_csv,
                                 #          get_formulation_means
    similarity.py                # f1(), f2() — pure math, no numpy
    loader.py                    # load_dissolution_csv(), get_formulation_means(),
                                 #   DissolutionCSVConfig (pydantic)
    study.py                     # DissolutionStudy, ComparisonResult
    bootstrap.py                 # bootstrap_f2(), BootstrapF2Result
    plotting.py                  # dissolution_profile_plot_b64() — used internally by html.py
    reporting.py                 # render_markdown_report(), report_dissolution()

  report/
    __init__.py
    html.py                      # render_html_report() — Jinja2, injects zip() into env.globals
    templates/
      dissolution_report.html    # Navy header, PASS/FAIL badges, embedded base64 plot, disclaimer

  datasets/
    __init__.py                  # example_dissolution_path(), example_similar_path(),
                                 #   example_not_similar_path()
    example_dissolution.csv
    example_similar.csv
    example_not_similar.csv

  nca/, sim/, pop/, bayes/, ml/, validation/  # stubs only, not yet implemented
```

---

## Dissolution data flow

```
CSV file
  -> load_dissolution_csv()        pydantic-validated DataFrame
  -> DissolutionStudy.from_csv()   wraps DataFrame
  -> study.compare(ref, test)      get_formulation_means() per label -> f1/f2
  -> ComparisonResult              dataclass
  -> result.summary()              text to console
  -> result.report("out.html")     report_dissolution() -> render_html_report()
                                   -> dissolution_profile_plot_b64() embedded in HTML

  -> study.bootstrap_compare()     extracts vessel matrix from df -> bootstrap_f2()
  -> BootstrapF2Result             dataclass with CI
```

---

## CI / Release pipeline

- **CI:** `.github/workflows/ci.yml` — pytest matrix over Python 3.10/3.11/3.12 on every push/PR
- **Publish:** `.github/workflows/publish.yml` — triggers on `v*.*.*` tags
  - Job 1: build wheel + sdist, `twine check`
  - Job 2: publish to TestPyPI (environment: `testpypi`)
  - Job 3: publish to real PyPI (environment: `pypi`)
  - Uses OIDC Trusted Publishing — no stored tokens
- **Tag pattern:** `git tag v0.x.x && git push origin v0.x.x`

GitHub environments `testpypi` and `pypi` are configured. Trusted Publishers are registered at both test.pypi.org and pypi.org.

---

## Known gotchas (do not repeat these mistakes)

### 1. Windows cp1252 console — ASCII only in CLI output
Em dashes (`—`), right arrows (`→`), `>=`, `<=` cause `UnicodeEncodeError` on Windows cp1252 terminals. All CLI docstrings and `typer.echo()` output must use plain ASCII. Use `->`, `>=`, `-`.

### 2. Jinja2 does not expose Python builtins
`zip()` is not available in Jinja2 templates by default. It is manually injected in `report/html.py`:
```python
env.globals["zip"] = zip
```
Never remove this line, and add any other needed builtins the same way.

### 3. `.gitignore` blocks HTML templates and notebooks
The repo `.gitignore` has `*.html` and `*.ipynb`. Exceptions are declared:
- `!src/**/*.html` — allows the Jinja2 template to be committed
- `!demo.ipynb` — allows the demo notebook

If you add new HTML templates or notebooks, add explicit exceptions.

### 4. `datasets/__init__.py` uses functions, not constants
The old `EXAMPLE_DISSOLUTION_CSV` constant was replaced with `example_dissolution_path()`. Any code that imports the constant will fail. Always call the function.

### 5. `bootstrap_f2` is low-level — use `study.bootstrap_compare()` in user-facing code
`bootstrap_f2()` requires 2D numpy arrays. `DissolutionStudy.bootstrap_compare()` extracts those arrays from the loaded DataFrame automatically. User docs and demos should only show the high-level method.

### 6. `ComparisonResult.plot()` uses `matplotlib.use("Agg")`
The plot method sets the Agg backend before importing matplotlib, making it safe in headless environments. If a user is in a Jupyter notebook with an inline backend already active, they may need to call `%matplotlib inline` themselves after the plot renders.

### 7. GitHub username is `priyamthakar` — not `priyamthakar1`
`priyamthakar1` is the email prefix. The actual GitHub username is `priyamthakar`. All repo URLs must use the correct username.

---

## Test suite (78 tests as of v0.1.4)

```
tests/
  dissolution/
    test_similarity.py    f1/f2 validation, edge cases, regulatory method
    test_study.py         loader, DissolutionStudy, compare, 85% warning, CV warning, reports
    test_bootstrap.py     BootstrapF2Result, bootstrap_f2 happy/error paths
  test_cli.py             CLI commands
```

Run: `pytest` or `pytest --tb=short -q`

Single test: `pytest tests/dissolution/test_similarity.py::TestF2::test_identical_profiles`

---

## Next: v0.2.0 — Dissolution model fitting

This is the next major milestone. Planned scope:

```python
from openpkflow.dissolution import DissolutionStudy

study = DissolutionStudy.from_csv("data.csv")
fits = study.fit_models("reference", models=["weibull", "korsmeyer_peppas", "higuchi", "first_order", "zero_order"])
fits.summary()           # table: model, params, R2, AIC, BIC
fits.plot()              # profile + model overlays
fits.report("fit.html")  # HTML report with fit table and overlay plot
```

Implementation notes:
- Use `scipy.optimize.curve_fit` for each model
- Return params + R2 + AIC + BIC per model
- New file: `dissolution/models.py`
- HTML report gains a fit-results table and overlay plot on the profile
- Validation discipline: each model needs degenerate test + published reference (e.g., Weibull: Costa & Lobo 2001 Eur J Pharm Sci)

After v0.2.0: v0.3.0 (ReportLab PDF + python-docx Word), then v0.4.0 NCA.

---

## Positioning (memorize this)

**Use:**
> A transparent, reproducible, open-source Python workflow for dissolution, NCA, PK/PD simulation, and pharmacometric reporting.

**Never say:**
> "FDA-approved", "replaces Certara", "AI discovers the perfect formulation."

---

## Key references for pharmacometric correctness

- FDA 1997 Guidance: Dissolution Testing of Immediate Release Solid Oral Dosage Forms — f1/f2 definition and 85% rule
- Shah VP et al. (1998) Pharm Res 15(6):889-896 — bootstrap f2 methodology
- Davit BM et al. (2013) AAPS J 15(4):1150-1157 — bootstrap f2 regulatory context
- Costa P, Lobo JMS (2001) Eur J Pharm Sci 13:123-133 — dissolution model fitting reference
