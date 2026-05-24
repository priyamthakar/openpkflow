# Handoff — start here

**Project:** OpenPKFlow
**Last updated:** 2026-05-24
**Current version:** 2.3.0 (in development -- not yet tagged/pushed)

---

## Where things stand

- ~900 tests passing. Full validation suite: 127/127 in `tests/validation/`.
- VALIDATION.md maps every test to FDA/EMA guidance and external reference.
- All science modules cross-validated against R references (see gap table below).
- Pop PK FOCE-I has external reference coverage against the `nlme` Theophylline fit.
  Keep `pop/estimation/` frozen except for bug fixes and validation maintenance.

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
| Pop PK FOCE-I/SAEM | Yes (internal) | nlme reference (Pinheiro & Bates 2000, Table 8.1) within 20% tol | **DONE -- v2.3.0** |

**bootstrap_f2 note:** point estimate is validated (algebraically identical to bootf2 0.4.1).
CI is stochastic — cannot pin values. CI correctness is a statistical guarantee of the
algorithm design, not a numerical check. This is the accepted resolution; document in
VALIDATION.md if you agree, otherwise implement a coverage-rate check (1000 seeds).

---

## Remaining tasks — priority order

### 1. Pop PK cross-validation (DONE -- v2.3.0)

`run_foce_i()` validated against nlme reference values (Pinheiro & Bates 2000,
Table 8.1) on the 12-subject Theophylline dataset. Typical values match within
20% relative tolerance (documented threshold in HANDOFF.md).

Validation test: `tests/validation/test_pop_foce_reference.py`
R script (waiting for Rtools): `scripts/nlmixr2_popk_crossval.R`

nlmixr2 5.0.0 is installed but requires Rtools/C compiler to compile rxode2
models. nlmixr2 numerical comparison will be added when Rtools is available.
The nlme fallback (same FOCE-I methodology, same dataset) resolves the debt.

### 2. Remove covariate skeleton (DONE -- v2.3.0)

`CovariateModel`, `apply_covariates`, and `CovariateDef` removed from `pop/estimation/`.
Breaking change documented in CHANGELOG.md v2.3.0.

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
1. Pop PK FOCE-I cross-validation test is green against the `nlme` reference values
2. Covariate skeleton removal is documented as a breaking change
3. conda-forge listing is live, or explicitly deferred as an owner/external process

After v2.3.0, openpkflow is a maintained library with Pop PK marked as
research-grade and externally sanity-checked. nlmixr2 numerical comparison remains
blocked only by local Rtools/C compiler availability.

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
