# Handoff — start here

**Project:** OpenPKFlow
**Last updated:** 2026-05-24
**Current version:** 2.2.0 (tagged, pushed to GitHub + PyPI)

---

## Where things stand

- ~900 tests passing. Full validation suite: 127/127 in `tests/validation/`.
- VALIDATION.md maps every test to FDA/EMA guidance and external reference.
- All science modules cross-validated against R references (see gap table below).
- Pop PK (FOCE-I, SAEM) is the only remaining honesty debt. Do not extend it.

### Cross-validation summary (as of 2026-05-24)

| Module | Internal tests | External cross-val | Status |
|--------|---------------|--------------------|--------|
| NCA single-dose | Yes | PKNCA 0.12.1 + NonCompart 0.8.0 (3-way) | Done |
| NCA steady-state | Yes | PKNCA 0.12.1 | Done |
| NCA urinary (Ae, CLr) | Yes | Independent R formula (algebraic) | Done |
| Dissolution f1/f2 | Yes | bootf2 0.4.1 | Done |
| Dissolution bootstrap_f2 | Yes | Point estimate only (CI stochastic) | Done — see note |
| Dissolution model fitting | Yes | Base R lm/optim (all 5 models) | Done |
| IVIVC WN + LR | Yes | Independent R formula (algebraic) | Done |
| IVIVC convolution + Levy | Yes (internal) | None | Low (numerical convolution) |
| Sim 1-cmt/2-cmt | Yes (Gibaldi & Perrier) | None | Low (math self-validates) |
| BE/TOST | Yes (closed-form) | None | Low (exact analytical) |
| BE/TOST power/n | Yes (internal) | None | Medium — PowerTOST R pkg |
| Pop PK FOCE-I/SAEM | Yes (internal) | None | **HONESTY DEBT — blocks v2.3.0** |

**bootstrap_f2 note:** point estimate is validated (algebraically identical to bootf2 0.4.1).
CI is stochastic — cannot pin values. CI correctness is a statistical guarantee of the
algorithm design, not a numerical check. This is the accepted resolution; document in
VALIDATION.md if you agree, otherwise implement a coverage-rate check (1000 seeds).

---

## Remaining tasks — priority order

### 1. Pop PK cross-validation (honesty debt — blocks v2.3.0)

The only substantive remaining blocker. `run_foce_i()` and `run_saem()` in
`pop/estimation/` have not been verified against any external reference.
README carries a "research-grade" caveat. Per CLAUDE.md, no new pop PK features
can ship until cross-validation lands.

**nlmixr2 5.0.0 is installed and ready.** No setup needed.

- Reference dataset: Theophylline pop PK (Pinheiro & Bates 2000, Table A.1)
  — same 12-subject theoph dataset used for NCA cross-validation
  — available at `src/openpkflow/datasets/theoph.csv`
- Write: `scripts/nlmixr2_popk_crossval.R` + `tests/validation/test_pop_foce_reference.py`
- Pattern: same tolerance strategy as all other cross-vals; pop PK estimates differ slightly
  between implementations so use 10-20% relative tolerance (not 1e-8)
- Template R script: `scripts/pknca_theoph_crossval.R` (same dataset, similar output format)
- Template test file: `tests/validation/test_nca_theoph_reference.py`
- Add entry to VALIDATION.md; mark done in this file

### 2. Remove covariate skeleton (technical debt — v2.3.0 breaking change)

`CovariateModel` and `apply_covariates` in `pop/estimation/` are on PyPI but
silently do nothing when passed to `run_foce_i` or `run_saem`.
A `DeprecationWarning` was added in v2.2.0.

**Plan:**
1. Delete `pop/estimation/covariates.py` (or wherever the skeleton lives)
2. Remove imports/exports from `pop/estimation/__init__.py`
3. Update CHANGELOG.md: document as breaking change in v2.3.0
4. Bump version in `pyproject.toml` to `2.3.0`
5. Confirm `ruff check`, `ruff format`, `mypy --strict` clean
6. Run full test suite; confirm no tests depend on the removed symbols

**Do this after pop PK cross-validation lands** so both changes go in v2.3.0 together.

### 3. Submit conda-forge recipe (distribution — owner action required)

`scripts/conda-forge/meta.yaml` is complete. sha256 is the real v2.2.0 hash
(`e611165358b7913f9455c0a8a3ded323be870763f2d2a9fa5d438c4055c7bfa5`).

**Steps:**
1. Fork `https://github.com/conda-forge/staged-recipes`
2. Create `recipes/openpkflow/meta.yaml` — copy from `scripts/conda-forge/meta.yaml`
3. Open PR following conda-forge contributing guide
4. Maintainer review takes days to weeks — this is an async external process

A Claude Code agent can write and stage the PR; the owner (Priyam) must submit it
and respond to maintainer review comments.

### 4. BE/TOST power cross-validation vs PowerTOST (nice-to-have, ~3h)

Medium-priority validation. `install.packages("PowerTOST")` in R, then:
- Write: `scripts/powertost_crossval.R` + `tests/validation/test_be_power_reference.py`
- Template: `tests/validation/test_dissolution_bootf2_reference.py`
- Add entry to VALIDATION.md

---

## What "project complete" looks like

v2.3.0 ships when:
1. Pop PK cross-validated against nlmixr2 (**the real remaining work**)
2. Covariate skeleton removed (documented breaking change)
3. conda-forge listing live (after maintainer review)

After v2.3.0, openpkflow is a maintained library — no more honesty debt,
all science modules validated, full distribution coverage.

---

## Architecture reference

- `pop/estimation/__init__.py` — full architecture narrative for the estimation module
- `VALIDATION.md` — test-to-guidance cross-reference
- `V2_ARCHITECTURE_DECISION.md` — v2.0.0 Bayesian PK decision record (historical)
- `CLAUDE.md` — authoritative rules for AI agents (scope, conventions, correctness rules)

---

## R environment (Windows)

R is installed at `C:\Program Files\R\R-4.6.0\`. Library path: `D:/R-library/4.6`

Run R scripts:
```
"C:\Program Files\R\R-4.6.0\bin\Rscript.exe" scripts/<name>.R
```

Packages installed: PKNCA 0.12.1, NonCompart 0.8.0, bootf2 0.4.1, nlmixr2 5.0.0

Run all tests (excluding slow MCMC):
```
pytest --ignore=tests/pop/test_saem.py --ignore=tests/bayes/test_bayes_be.py -k "not MCMC and not mcmc"
```

Run validation suite only (fast, 127 tests):
```
pytest tests/validation/ -q
```

---

## Definition of done (any new validation test)

1. Test cites DOI or R package + version in docstring
2. Tolerance is justified by the formula or optimizer
3. `ruff check`, `ruff format`, `mypy --strict` clean
4. Entry added to VALIDATION.md
5. This file updated to mark task done
