# Handoff — start here

**Project:** OpenPKFlow v2.2.0
**Last updated:** 2026-05-23

---

## Where things stand

- v2.2.0 tagged and pushed to GitHub + PyPI. CHANGELOG complete.
- 900 tests (866 passing, 15 skipped, 1 pre-existing CLI version string stale).
  Benchmarks excluded from headless CI.
- VALIDATION.md — 49 test files mapped to FDA/EMA guidance (PKNCA cross-val added).
- PKNCA-R cross-validation scaffolded: `tests/validation/test_nca_theoph_reference.py`
  has a `TestPKNCACrossValidation` class with ≤2% tolerance checks on all 12 subjects.
  `scripts/pknca_theoph_crossval.R` is ready to run. The `_PKNCA_REFERENCE` dict
  needs a live PKNCA 0.10.x run to replace the placeholder openpkflow values.
- conda-forge recipe drafted at `scripts/conda-forge/meta.yaml`. Noarch Python,
  `matplotlib-base`, hatchling build. sha256 placeholder needs filling before
  PR to `conda-forge/staged-recipes`.
- README comparison table verified and corrected: CDISC PP row split, PKNCA no
  longer claiming CDISC PP, research-grade caveat added to pop PK rows, test
  count fixed (648 → 900).
- Pop estimation (FOCE-I, SAEM) shipped but NOT cross-validated against NONMEM
  or nlmixr2. README discloses this; estimation scope is frozen.
- Covariate API (`CovariateModel`, `apply_covariates`) shipped in v2.2.0 as a
  non-functional skeleton. It does not affect estimation results. A
  `DeprecationWarning` is emitted on import. Tracked for removal in v2.3.0.

---

## Next tasks

1. **Run PKNCA-R** — execute `Rscript scripts/pknca_theoph_crossval.R` in an
   environment with R + PKNCA 0.10.x, paste the output `_PKNCA_REFERENCE` dict
   into `tests/validation/test_nca_theoph_reference.py`, run the test suite to
   confirm ≤2% agreement. R is not installed in CI; this is a one-time manual step.

2. **Submit conda-forge recipe** — compute `sha256sum dist/openpkflow-2.2.0.tar.gz`,
   fill the placeholder in `scripts/conda-forge/meta.yaml`, submit single PR to
   `conda-forge/staged-recipes`.

3. **Pre-existing CLI test** — `tests/test_cli.py::test_version` asserts `"2.0.0"`
   but the package is `2.2.0`. Fix the assertion to match the live `pyproject.toml`
   version string.

---

## Honesty debt (must resolve before any new module)

- **Covariate skeleton**: `CovariateModel` and `apply_covariates` are on PyPI but
  silently do nothing when passed to `run_foce_i` or `run_saem`. DeprecationWarning
  added in v2.2.0. Plan: remove entirely in v2.3.0 as a documented breaking change.
- **Pop estimation unvalidated**: `run_foce_i` and `run_saem` have not been
  independently verified against NONMEM or nlmixr2 on a reference dataset. The
  README pop PK section carries a "research-grade" caveat. Do not add estimation
  features until cross-validation lands.

---

## Out of scope

See **"Scope and boundary"** in CLAUDE.md — that is the authoritative list.
This file does not duplicate it.

---

## New files created (2026-05-23 maintenance)

| File | Purpose |
|------|---------|
| `scripts/pknca_theoph_crossval.R` | PKNCA 0.10.x R script — reads theoph.csv, outputs `_PKNCA_REFERENCE` dict |
| `scripts/conda-forge/meta.yaml` | conda-forge recipe (noarch, hatchling, matplotlib-base) |

## Files modified (2026-05-23 maintenance)

| File | Change |
|------|--------|
| `tests/validation/test_nca_theoph_reference.py` | Rewritten: removed inline mg/kg data, uses `NCAStudy.from_csv()` on full 12-subject theoph.csv, added `TestPKNCACrossValidation` with ≤2% tolerance per subject |
| `README.md` | Split CDISC PP row (PKNCA no longer claims it), added research-grade caveat on pop PK rows, fixed test count 648→900 |

---

## Architecture reference

See module docstrings and CLAUDE.md. In particular:
- `pop/estimation/__init__.py` — full architecture narrative for the estimation module
- `VALIDATION.md` — test-to-guidance cross-reference
- `V2_ARCHITECTURE_DECISION.md` — v2.0.0 Bayesian PK decision record (historical)
