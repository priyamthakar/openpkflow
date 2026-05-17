# Changelog

All notable changes to OpenPKFlow will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

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
