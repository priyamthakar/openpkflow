# Handoff — start here

**Project:** OpenPKFlow v2.2.0
**Last updated:** 2026-05-24

---

## Where things stand

- v2.2.0 tagged and pushed to GitHub + PyPI. CHANGELOG complete.
- ~900 tests passing. Benchmarks excluded from headless CI.
- VALIDATION.md — all test files mapped to FDA/EMA guidance (updated 2026-05-24).
- **Three-way NCA cross-validation complete** (strongest available open-source claim):
  - PKNCA 0.12.1 (primary + extended): 12 subjects, 11 parameters each, ≤2% tolerance.
    Scripts: `scripts/pknca_theoph_crossval.R`, `scripts/pknca_theoph_crossval_extended.R`
    Tests: `tests/validation/test_nca_theoph_reference.py` (both `TestPKNCACrossValidation`
    and `TestPKNCAExtendedCrossValidation`).
  - NonCompart 0.8.0: independent second reference, all 12 theoph subjects, all parameters.
    Script: `scripts/noncompart_theoph_crossval.R`
    Test: `tests/validation/test_nca_noncompart_reference.py`
  - openpkflow == PKNCA == NonCompart to 4+ decimal places on all subjects/parameters.
- **Steady-state NCA cross-validated** against PKNCA 0.12.1:
  - Synthetic SS dataset: `src/openpkflow/datasets/ss_crossval.csv` (3 subjects, true SS)
  - Script: `scripts/pknca_ss_crossval.R`
  - Test: `tests/validation/test_nca_ss_reference.py`
  - **Swing unit convention documented**: openpkflow = dimensionless ratio (WinNonlin);
    PKNCA = percentage (x100). Documented in `nca/results.py` and `nca/methods.py`.
- **Dissolution f2 cross-validated** against bootf2 0.4.1:
  - Script: `scripts/bootf2_dissolution_crossval.R`
  - Test: `tests/validation/test_dissolution_bootf2_reference.py`
  - bootf2 `calcf2(f2.type="est.f2")` is algebraically identical to openpkflow
    `f2(method="all_points")`; values match to floating-point precision (< 1e-10).
- conda-forge recipe at `scripts/conda-forge/meta.yaml`: sha256 filled with real
  v2.2.0 hash (`e611165358b7913f9455c0a8a3ded323be870763f2d2a9fa5d438c4055c7bfa5`).
  Still needs PR submission to `conda-forge/staged-recipes`.
- Pop estimation (FOCE-I, SAEM) shipped but NOT cross-validated against NONMEM
  or nlmixr2. README discloses this; estimation scope is frozen.
- Covariate API (`CovariateModel`, `apply_covariates`) shipped in v2.2.0 as a
  non-functional skeleton. `DeprecationWarning` emitted on import. Tracked for
  removal in v2.3.0.

---

## Next tasks (priority order)

1. **Submit conda-forge recipe** — submit single PR to `conda-forge/staged-recipes`
   using `scripts/conda-forge/meta.yaml` (sha256 already filled with v2.2.0 hash).
   This is the only major distribution task remaining.

2. **CLI version test** — `tests/test_cli.py::test_version` may assert an old version
   string. Verify it matches the live `pyproject.toml` version (`2.2.0`).

3. **Bootstrap f2 stochastic validation** — `bootstrap_f2()` CI was not validated
   stochastically against `bootf2::bootf2()` (the bootstrap CI is stochastic so
   values can't be pinned). Options: (a) run coverage check across many seeds and
   verify 90% CI includes true f2 in >90% of runs, or (b) accept that the f2_observed
   point estimate is validated (done) and CI coverage is a statistical guarantee of
   the algorithm design rather than a numerical check.

4. **Pop PK validation** — `run_foce_i` and `run_saem` are unvalidated against NONMEM
   or nlmixr2. Largest remaining honesty gap. Do not add pop PK features until
   cross-validation lands. This requires NONMEM license or nlmixr2 R install plus a
   reference pop PK dataset (e.g., Theophylline pop PK from Pinheiro & Bates).

5. **BE/TOST power/sample-size vs PowerTOST** — medium priority; current tests use
   closed-form truth for TOST. PowerTOST R package could cross-validate the power
   calculation if installed. `install.packages("PowerTOST")` then write
   `scripts/powertost_crossval.R` + `tests/validation/test_be_power_reference.py`.

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

## Validation gap analysis (as of 2026-05-24)

| Module | Internal tests | External cross-val | Status |
|--------|---------------|-------------------|--------|
| NCA single-dose | Yes | PKNCA 0.12.1 + NonCompart 0.8.0 (3-way) | Done |
| NCA steady-state | Yes | PKNCA 0.12.1 | Done |
| NCA urinary (Ae, CLr) | Yes | Independent R formula (algebraic) | Done |
| Dissolution f1/f2 | Yes | bootf2 0.4.1 | Done |
| Dissolution bootstrap_f2 | Yes | Point estimate only (CI stochastic) | Partial |
| Dissolution model fitting | Yes | Base R lm/optim (all 5 models) | Done |
| IVIVC WN + LR | Yes | Independent R formula (algebraic) | Done |
| IVIVC convolution + Levy | Yes (internal) | None | Low (numerical convolution) |
| Sim 1-cmt/2-cmt | Yes (Gibaldi & Perrier) | None | Low (math self-validates) |
| BE/TOST TOST | Yes (closed-form) | None | Low (exact analytical) |
| BE/TOST power/n | Yes (internal) | None | Medium (PowerTOST R pkg) |
| Pop PK FOCE-I/SAEM | Yes (internal) | None | **HONESTY DEBT — no features until done** |

---

## Out of scope

See **"Scope and boundary"** in CLAUDE.md — that is the authoritative list.
This file does not duplicate it.

---

## New files created (2026-05-24 session)

| File | Purpose |
|------|---------|
| `scripts/pknca_theoph_crossval_extended.R` | PKNCA 0.12.1 — full NCA parameter set (AUCinf, lambda_z, CL_F, Vz_F, etc.) |
| `scripts/pknca_ss_crossval.R` | PKNCA 0.12.1 steady-state NCA on synthetic SS dataset |
| `scripts/noncompart_theoph_crossval.R` | NonCompart 0.8.0 — independent 3rd-party NCA validation |
| `scripts/bootf2_dissolution_crossval.R` | bootf2 0.4.1 — dissolution f2 cross-validation |
| `scripts/probe_bootf2.R` | One-time bootf2 API probe (historical, not needed again) |
| `src/openpkflow/datasets/ss_crossval.csv` | Synthetic steady-state dataset (3 subjects, true C(0)=C(tau)) |
| `tests/validation/test_nca_ss_reference.py` | PKNCA SS cross-validation tests (11 tests) |
| `tests/validation/test_nca_noncompart_reference.py` | NonCompart 3-way agreement tests (12 tests) |
| `tests/validation/test_dissolution_bootf2_reference.py` | bootf2 dissolution f2 tests (10 tests) |

## Files modified (2026-05-24 session)

| File | Change |
|------|--------|
| `tests/validation/test_nca_theoph_reference.py` | Added `TestPKNCAExtendedCrossValidation` (9 tests for AUCinf, lambda_z, CL_F, Vz_F, etc.); fixed version strings "0.10.x" -> "0.12.1" throughout |
| `src/openpkflow/nca/results.py` | Documented swing as dimensionless ratio; PKNCA comparison note |
| `src/openpkflow/nca/methods.py` | Updated `steady_state_parameters()` docstring: swing convention explanation |
| `src/openpkflow/datasets/__init__.py` | Added `example_ss_crossval_path()` |
| `scripts/conda-forge/meta.yaml` | sha256 placeholder -> real v2.2.0 hash |

## Files modified (2026-05-23 maintenance)

| File | Change |
|------|--------|
| `tests/validation/test_nca_theoph_reference.py` | Rewritten: removed inline mg/kg data, uses `NCAStudy.from_csv()` on full 12-subject theoph.csv, added `TestPKNCACrossValidation` with ≤2% tolerance per subject |
| `README.md` | Split CDISC PP row (PKNCA no longer claims it), added research-grade caveat on pop PK rows, fixed test count |

---

## Architecture reference

See module docstrings and CLAUDE.md. In particular:
- `pop/estimation/__init__.py` — full architecture narrative for the estimation module
- `VALIDATION.md` — test-to-guidance cross-reference (updated 2026-05-24)
- `V2_ARCHITECTURE_DECISION.md` — v2.0.0 Bayesian PK decision record (historical)

## R environment (Windows)

R is installed at `C:\Program Files\R\R-4.6.0\`. Library path: `D:/R-library/4.6`.
Run R scripts with:
```
"C:\Program Files\R\R-4.6.0\bin\Rscript.exe" scripts/<name>.R
```
Packages installed: PKNCA 0.12.1, NonCompart 0.8.0, bootf2 0.4.1.
Unit note for NonCompart `sNCA()`: pass `concUnit="mg/L"` to get CL in L/h and V in L.
Without `concUnit`, NonCompart defaults to mL/h and mL (1000x larger).
