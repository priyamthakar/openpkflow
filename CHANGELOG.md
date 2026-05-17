# Changelog

All notable changes to OpenPKFlow will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

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
