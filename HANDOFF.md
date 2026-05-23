# Handoff — start here

**Project:** OpenPKFlow v2.2.0
**Last updated:** 2026-05-23

---

## Where things stand

- v2.2.0 tagged and pushed to GitHub + PyPI. CHANGELOG complete.
- 874 tests passing (15 skipped). Benchmarks included.
- VALIDATION.md added — 48 test files mapped to FDA/EMA guidance.
- Theoph NCA benchmark in `tests/validation/`: internal-consistency only.
  PKNCA-R cross-validation is pending a controlled R run (see task 2 below).
- Pop estimation (FOCE-I, SAEM) shipped but NOT cross-validated against NONMEM
  or nlmixr2. README discloses this; estimation scope is frozen.
- Covariate API (`CovariateModel`, `apply_covariates`) shipped in v2.2.0 as a
  non-functional skeleton. It does not affect estimation results. A
  `DeprecationWarning` is emitted on import. Tracked for removal in v2.3.0.

---

## Next 3 tasks, in order

1. **PKNCA-R cross-validation** — run PKNCA 0.10.x in R on the identical theoph
   dataset, extract per-subject AUClast and Cmax, update
   `tests/validation/test_nca_theoph_reference.py` with real reference values and
   a tight tolerance check (within 2%). This is the flagship evidence for the
   "transparent and reproducible" claim.

2. **conda-forge recipe** — ~3h, single PR to
   `conda-forge/staged-recipes`. Closes the distribution gap with the biostat
   community (pip-only is a barrier for many pharmacometrics groups). Template:
   follow `pknca` feedstock as a reference for a scipy-based pharmacometrics package.

3. **README "Comparison" table** — feature matrix vs PKNCA (R), WinNonlin, Pharmpy,
   OpenPKPD. Already marked as done in ROADMAP but not verified as live in README.
   Check and ship if missing.

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

## Architecture reference

See module docstrings and CLAUDE.md. In particular:
- `pop/estimation/__init__.py` — full architecture narrative for the estimation module
- `VALIDATION.md` — test-to-guidance cross-reference
- `V2_ARCHITECTURE_DECISION.md` — v2.0.0 Bayesian PK decision record (historical)
