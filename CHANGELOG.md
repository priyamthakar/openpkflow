# Changelog

All notable changes to OpenPKFlow will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

## [0.4.0] — 2026-05-18

### Added
- `nca/methods.py` — pure-math NCA layer: `auc_linear`, `auc_log`, `auc_linear_up_log_down` (linear-up/log-down), `cmax`, `tmax`, `lambda_z` (BAR² auto-selection and manual mode), `auc_inf_obs`, `auc_percent_extrapolated`, `clearance_volume_parameters`; `AUCResult` and `LambdaZResult` frozen dataclasses
- `nca/loader.py` — `load_nca_csv()`: CSV loader with full BLQ handling (none/drop/zero/half_lloq/lloq, m1/m2 aliases, `<0.5` string-BLQ parsing via regex)
- `nca/results.py` — `NCAResult` (per-subject) and `NCASummaryResults` dataclasses with `summary()`, `to_dict()`, `to_dataframe()`, `report()` methods; route-aware field naming (oral: CL_F/Vz_F, IV: CL/Vz)
- `nca/study.py` — `NCAStudy` with `__init__(df, ...)`, `from_csv(path, ...)`, and `analyze() -> NCASummaryResults`; explicit auc_method required; lambda_z failure handled gracefully (None + warning)
- `nca/reporting.py` — `report_nca_single()` and `report_nca_summary()` in HTML (Jinja2) and Markdown; PDF/DOCX deferred to v0.4.1
- `report/templates/nca_single_report.html` — per-subject NCA HTML report with navy header, PK parameter table, warnings panel, disclaimer
- `report/templates/nca_summary_report.html` — multi-subject summary HTML report with tabular results
- `datasets/theoph.csv` — R nlme::Theoph reference dataset (12 subjects, 11 timepoints, oral theophylline, doses precomputed in mg)
- `datasets/__init__.py` — adds `example_theoph_path()`
- 93 NCA tests: `tests/nca/test_methods.py` (unit tests for all math functions with hand-checked expected values), `test_loader.py` (BLQ handling, edge cases), `test_study.py` (integration), `test_theoph_reference.py` (regression suite against Theoph dataset)

### Changed
- `nca/__init__.py` wired up to export all public NCA symbols
- `datasets/__init__.py` adds `example_theoph_path()` to `__all__`

### Implementation notes
- AUC dispatch asymmetry: `auc_linear` returns `float`; `auc_log` and `auc_linear_up_log_down` return `AUCResult` — handled in NCAStudy.analyze()
- BAR² lambda_z algorithm: enumerates all tail windows anchored at last quantifiable point, post-Cmax positive only, selects by adjusted R² descending then more points then longer span (mirrors PKNCA R package)
- NaN handling contract: loader cleans arrays; AUC math functions assume clean input
- Theoph regression values: AUClast mean ~100.1, Cmax mean ~8.89, half_life mean ~7.89 h — linear_up_log_down, no BLQ handling

## [0.3.0] — 2026-05-18

### Added
- `render_comparison_pdf_report()` in `report/pdf.py` — ReportLab PDF for dissolution comparison; navy-header table, embedded profile plot, disclaimer
- `render_model_fit_pdf_report()` in `report/pdf.py` — ReportLab PDF for model fit; ranked table with gold best-row highlight, fit overlay plot, dual disclaimer
- `render_comparison_docx_report()` in `report/docx.py` — python-docx Word document for dissolution comparison; summary + data tables, embedded plot, italic disclaimer
- `render_model_fit_docx_report()` in `report/docx.py` — python-docx Word document for model fit; ranked table with bold best row, failed-models note, fit overlay plot, dual disclaimer
- `ComparisonResult.report(format="pdf"|"docx")` — PDF and Word export from study comparison
- `DissolutionFitResults.report(format="pdf"|"docx")` — PDF and Word export from model fitting
- `report_dissolution(format="pdf"|"docx")` dispatcher arms in `dissolution/reporting.py`
- CLI format inference: `.pdf` -> `"pdf"`, `.docx` -> `"docx"` (in addition to existing `.md` -> `"markdown"`, else `"html"`)
- 19 new tests in `tests/report/test_pdf.py` and `tests/report/test_docx.py`: magic-byte assertions, file size, `tmp_path` write, round-trip disclaimer check via python-docx, `pytest.importorskip` skip guard

### Changed
- CI matrix now installs `.[dev,reports]` so reportlab and python-docx are available in test runs
- `DissolutionFitResults.report()` return type widened to `str | bytes`
- `ComparisonResult.report()` and `report_dissolution()` return type widened to `str | bytes`

### Implementation notes
- Both renderers use lazy imports inside function bodies; module top is stdlib only
- Import guard raises `ImportError("... pip install openpkflow[reports]")` if extra not installed
- Plot embedding: `base64.b64decode(plot_b64)` -> `io.BytesIO` -> `Image`/`add_picture`
- All docstrings ASCII-only; rendered document content may use unicode

## [0.2.0] — 2026-05-18

### Added
- `DissolutionStudy.fit_models(formulation, models=None)` — fits one or more standard release models to the mean profile of a formulation; returns `DissolutionFitResults`
- `fit_dissolution_models(time_points, observed_mean, formulation_label, models=None)` — low-level public API for fitting without a loaded CSV
- Five dissolution release models: `zero_order`, `first_order`, `higuchi`, `korsmeyer_peppas`, `weibull`
- `ModelFit` frozen dataclass — fit result per model: params, R2, AIC, AICc, BIC, converged flag, `predict()`, `to_dict()`
- `DissolutionFitResults` dataclass — ranked fit container: `.best` (lowest AICc), `.summary()`, `.plot()`, `.report()`, `.to_dict()`
- `DissolutionFitResults.plot()` — overlay plot of observed mean + fitted curves, ranked by AICc
- `DissolutionFitResults.report("fit.html")` — HTML report with fit table, overlay plot, and regulatory disclaimer
- `dissolution_fit_plot_b64()` in `plotting.py` — base64 PNG for HTML report embedding
- `render_model_fit_html_report()` in `report/html.py` — Jinja2 renderer for `fit_report.html`
- `report/templates/fit_report.html` — navy-header HTML template matching existing dissolution report style
- Korsmeyer-Peppas 60% rule: `UserWarning` when >1 timepoint exceeds 60% release
- Weibull empirical-model note added to report and docstring per FDA/EMA guidance
- All five models exported from `openpkflow.dissolution`: `ModelFit`, `DissolutionFitResults`, `fit_dissolution_models`

### Implementation notes
- Models fitted to mean profile; per-vessel fitting is future scope
- Model ranking by AICc, the small-sample-corrected information criterion; AIC and BIC also returned
- R2 reported for familiarity but not used for selection — it is misleading for nonlinear models
- Each model has data-driven initial-guess and bounds helpers to prevent degenerate fits
- Failed fits included in results with `converged=False`; excluded from ranking and plots
- Reference: Costa P, Lobo JMS (2001) Eur J Pharm Sci 13(2):123-133. DOI: 10.1016/S0928-0987(01)00095-1

## [0.1.4] — 2026-05-18

### Added
- `DissolutionStudy.bootstrap_compare(reference, test, ...)` — runs bootstrap f2 directly from loaded CSV data
- `ComparisonResult.plot(output_path, show)` — plots reference vs test profile with f1/f2 in title
- `demo.ipynb` rewritten: only openpkflow imports, clean 7-section workflow

## [0.1.3] — 2026-05-18

### Added
- `f2(method="regulatory")` option — trims timepoints per the FDA 85% rule; at most one timepoint where both profiles exceed 85% may be included; raises ValueError if fewer than 3 points remain
- CV% warning in `DissolutionStudy.compare()` — warns when coefficient of variation exceeds FDA limits: CV > 20% at early timepoints (<=15 min) or CV > 10% at later timepoints

### Changed
- README: removed em dashes and minimised parentheses; updated status table to reflect v0.1.1 deliverables; softened validation claims
- 78 tests passing

## [0.1.2] — 2026-05-18

### Added
- PyPI Trusted Publishing via GitHub Actions (`publish.yml`) — triggers on version tags, publishes to TestPyPI then PyPI using OIDC (no stored tokens)

## [0.1.1] — 2026-05-18

### Added
- `dissolution.bootstrap_f2()` — bootstrap CI for f2 (Shah 1998, Davit 2013); suitable for small-sample (<12 vessel) similarity assessment
- `dissolution.plotting.dissolution_profile_plot_b64()` — embedded matplotlib profile plot in HTML reports
- HTML reports now include a dissolution profile chart (reference vs test, 85% threshold line)
- `datasets.example_similar_path()` — example dataset with f2 ~80 (clearly similar profiles)
- `datasets.example_not_similar_path()` — example dataset with f2 ~38 (clearly dissimilar profiles)
- `py.typed` marker (PEP 561) — enables mypy type checking in downstream projects
- GitHub Actions CI — matrix build across Python 3.10, 3.11, 3.12

### Changed
- `datasets/__init__.py` — constants replaced with `example_dissolution_path()`, `example_similar_path()`, `example_not_similar_path()` functions using `importlib.resources`
- CLAUDE.md — added Commands section, data flow diagram, Windows ASCII constraint note

## [0.1.0] — 2026-05-17

### Added
- `dissolution.f1()` — difference factor (FDA/EMA dissolution guidance)
- `dissolution.f2()` — similarity factor (FDA/EMA dissolution guidance)
- `dissolution.DissolutionProfile` — validated data container for a single dissolution profile
- `dissolution.DissolutionStudy` — high-level study object: load CSV, compare, fit, report
- `dissolution.loader` — CSV ingestion with schema validation
- `dissolution.reporting` — Markdown and HTML report generation
- CLI command `openpkflow similarity` for f1/f2 from terminal
- CLI command `openpkflow version`
- Example dataset `datasets/example_dissolution.csv`
- Example script `examples/dissolution_basic.py`
- Full test suite with reference validation examples

### Notes
- f1/f2 require caller to supply matched, time-aligned percent-release values
- No external GUI or enterprise platform connectivity in this release
- Disclaimer: open-source research workflow; final regulatory interpretation requires expert review
