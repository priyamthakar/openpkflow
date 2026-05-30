# Handoff — start here

**Project:** OpenPKFlow
**Last updated:** 2026-05-30
**Current target version:** 2.4.0 release candidate

---

## Latest handoff update -- 2026-05-30, v2.4 credibility sprint

This section supersedes the older v2.3 notes below for current release work.
Start every takeover by running:

```powershell
git status --short --branch
git log --oneline -5
```

### What is already completed and pushed

- `0d923ae feat(be): add replicate design screening`
  - Added research-grade replicate BE screening in `src/openpkflow/be/replicate.py`.
  - Added `replicate_be`, `ReplicateBEResult`, CV helpers, EMA scaled-limit summaries, and unit coverage.
  - Kept labels explicitly caveated as screening, not validated formal RSABE.
- `afe6889 docs: add v2.4 credibility sprint to future plans`
  - Updated `FUTURE_PLANS.md` with the v2.4 credibility sprint plan.
- `6151dde feat(be): add replicate cli and release checks`
  - Added `openpkflow be replicate ... --report ... --json ...`.
  - Added replicate BE Markdown/HTML reporting and `examples/replicate_be_partial.csv`.
  - Added scalar reference validation in `tests/validation/test_be_replicate_reference.py`.
  - Added `RELEASE.md`, `.github/workflows/slow-validation.yml`, and slow-test marker configuration.
- `c9a0c7e ci: allow benchmark history push`
  - Added `contents: write` permission for benchmark history push.
  - GitHub Actions were green for this commit:
    - CI run `26677773546`: success.
    - Deploy Docs run `26677773556`: success.

### Release-finalization work included in this handoff

- Version bumped to `2.4.0` in `pyproject.toml` and `src/openpkflow/__init__.py`.
- `docs/changelog.md` now has `## [2.4.0] -- 2026-05-30`.
- Root `CHANGELOG.md` now has `## [2.4.0] -- 2026-05-30` with v2.4 replicate BE and release-readiness items.
- `README.md` now advertises replicate BE screening as `v2.4.0`, while keeping formal BE ANOVA / validated RSABE out of scope.
- `docs/validation-matrix.md` clarifies replicate BE scalar fixture validation and avoids claiming full RSABE parity.
- `tests/validation/test_be_replicate_reference.py` points to `scripts/replicate_be_crossval.R` for fixture regeneration.
- `tests/nca/test_methods_hypothesis.py` has two Hypothesis assumptions tightened to avoid invalid generated examples.
- Added `scripts/release_readiness.py`, a read-only release gate checker for version/changelog/git/tag/release state.
- Added `scripts/replicate_be_crossval.R`, an R-side scalar fixture generator for replicate BE screening values.

### Verification already run locally

- `python -m ruff check src tests scripts` passed after fixing import order in `scripts/release_readiness.py`.
- `python -m pytest tests\nca\test_methods_hypothesis.py::TestAUCLogInvariants tests\nca\test_methods_hypothesis.py::TestLambdaZ -q` passed: `9 passed`.
- `python -m pytest -q` passed: `1208 passed, 6 skipped, 22 deselected`.
- `python -m mkdocs build --strict` passed.
- `python -m build` passed and produced the `openpkflow-2.4.0` sdist and wheel.
- `python scripts\release_readiness.py` currently fails while the worktree is dirty and warns until tag/release exist. After commit, rerun it; warnings about missing `v2.4.0` tag and GitHub release are expected until release steps are performed.

### Known gaps before tagging v2.4.0

- Slow validation was started but not completed before interruption. Rerun:

```powershell
python -m pytest -m slow tests\validation -q
```

- `Rscript scripts\replicate_be_crossval.R` failed because `Rscript` is not on `PATH`. R is available on this machine; try:

```powershell
& "C:\Program Files\R\R-4.6.0\bin\Rscript.exe" scripts\replicate_be_crossval.R
```

- Do not tag or publish until the final commit is pushed, CI is green, slow validation is either green or explicitly deferred, and `python scripts\release_readiness.py` has no unexpected failures.
- After final release commit and green CI, create tag `v2.4.0`, let release automation run, then verify the GitHub release/PyPI artifacts.

### Prompt for next agent

```text
You are taking over OpenPKFlow in D:\openpkflow. The user wants the v2.4 credibility sprint finished and released only after proper verification. Start with `git status --short --branch` and `git log --oneline -5`. Read the top "Latest handoff update" section in HANDOFF.md first.

Current objective:
1. Verify the v2.4 release-finalization commit is present and pushed.
2. Run `python scripts\release_readiness.py`; expect tag/release warnings only before release.
3. Run or explicitly triage `python -m pytest -m slow tests\validation -q`.
4. Use the full Rscript path if regenerating replicate BE fixtures: `C:\Program Files\R\R-4.6.0\bin\Rscript.exe`.
5. Confirm GitHub Actions are green for the final commit.
6. Only then create/push tag `v2.4.0` and verify release artifacts.

Do not overclaim RSABE. OpenPKFlow v2.4 provides transparent replicate BE screening/reporting with scalar fixture validation; formal regulator-grade RSABE parity remains out of scope until jurisdiction-specific mixed-model/upper-bound parity is validated.
```

---

## Where things stand

- ~900 tests passing. Full validation suite: 190/190 in `tests/validation/`.
- VALIDATION.md maps every test to FDA/EMA guidance and external reference.
- All science modules cross-validated against R references (see gap table below).
- Pop PK FOCE-I has external reference coverage against the `nlme` Theophylline fit.
  Keep `pop/estimation/` frozen except for bug fixes and validation maintenance.

### Cross-validation summary (as of 2026-05-29)

| Module | Internal tests | External cross-val | Status |
|--------|---------------|--------------------|--------|
| NCA single-dose | Yes | PKNCA 0.12.1 + NonCompart 0.8.0 + **Phoenix WinNonlin** (4-way) | **DONE -- 2026-05-29** |
| NCA steady-state | Yes | PKNCA 0.12.1 | Done |
| NCA urinary (Ae, CLr) | Yes | Independent R formula (algebraic) | Done |
| Dissolution f1/f2 | Yes | bootf2 0.4.1 | Done |
| Dissolution bootstrap_f2 | Yes | Point estimate only (CI stochastic) | Done — see note |
| Dissolution model fitting | Yes | Base R lm/optim (all 5 models) | Done |
| IVIVC WN + LR | Yes | Independent R formula (algebraic) | Done |
| IVIVC convolution + Levy | Yes (internal) | None | Low (numerical convolution) |
| Sim 1-cmt/2-cmt | Yes (Gibaldi & Perrier) | None | Low (math self-validates) |
| BE/TOST | Yes (closed-form) | None | Low (exact analytical) |
| BE/TOST power/n | Yes (internal) | PowerTOST 1.5-7 | Done -- v2.3.0 |
| Pop PK FOCE-I/SAEM | Yes (internal) | nlme reference (Pinheiro & Bates 2000, Table 8.1) within 20% tol | Done -- v2.3.0 |

**bootstrap_f2 note:** point estimate is validated (algebraically identical to bootf2 0.4.1).
CI is stochastic — cannot pin values. CI correctness is a statistical guarantee of the
algorithm design, not a numerical check. This is the accepted resolution; document in
VALIDATION.md if you agree, otherwise implement a coverage-rate check (1000 seeds).

---

## Documentation (DONE -- 2026-05-30)

### 6. Theory guide
`docs/theory.md` created with full LaTeX formula derivations for all modules:
NCA (trapezoidal rules, BAR², derived parameters), PK simulation (Bateman,
1-cmt/2-cmt), dissolution (f1, f2, models), IVIVC (WN, LR, convolution),
BE/TOST (power, sample size), pop PK (FOCE-I, SAEM, shrinkage), Bayesian PK
(MAP, MCMC, Bayesian BE). Added to MkDocs nav as top-level section.

### 7. Pop PK tutorial expanded
`docs/tutorials/pop.md` expanded from 101 lines (diagnostics-only) to full
tutorial covering FOCE-I and SAEM estimation with worked Theoph examples,
2-cmt models, CLI usage, and regulatory notes.

### 8. Migration cheatsheet augmented
`docs/migration-cheatsheet.md` — added C0 back-extrapolation and sparse NCA
rows, clarified SAEM entry.

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

### 3. Submit conda-forge recipe (DONE -- distribution)

`scripts/conda-forge/meta.yaml` submitted and accepted to conda-forge.
`conda install -c conda-forge openpkflow` is live.

### 4. BE/TOST power cross-validation (DONE -- v2.3.0)

`be_tost_power()` and `be_sample_size()` implemented using the exact non-central
t-distribution method (Phillips 1990; Diletti et al. 1991). Cross-validated against
PowerTOST 1.5-7 on 6 power scenarios and 6 sample size scenarios -- all match within
1e-5 (power) and exactly (sample size).

Validation test: `tests/validation/test_be_power_reference.py`
R script: `scripts/powertost_crossval.R`

### 5. Phoenix WinNonlin NCA cross-validation (DONE -- 2026-05-29)

Validated NCA against Phoenix WinNonlin (Certara) public reference data:
- Theoph (12 subjects, oral): AUClast linear/log, AUCINF, CL_F, Vz_F, Cmax, Tmax
  all within 2% for 12 subjects. Lambda_z/HL/Vz_F/%Extrap exclude S6 (WNL selects
  7 points via auto-selection vs BAR^2 selecting 3; 4.3% lambda_z gap documented).
- Indometh (6 subjects, IV): Cmax, Tmax, Lambda_z/HL for 5/6 subjects all pass.
  AUClast/AUCINF NOT tested -- WNL includes C0 back-extrapolation (17-31% gap),
  which is a known missing feature. See `test_auclast_c0_backext_not_implemented`.
- Dose unit discovery: WNL used nominal dose=320 mg for all Theoph subjects (not
  individual Dose*Wt from the dataset; Subject 9 diverges 16% if Dose*Wt used).

Validation test: `tests/validation/test_nca_winnonlin_reference.py` (18 tests)
Interactive script: `scripts/crossval_winnonlin.py`

**Known gap to address next:** C0 back-extrapolation for IV bolus when no t=0
measurement exists. See `tests/validation/test_nca_winnonlin_reference.py::
TestWinNonLinIndometh::test_auclast_c0_backext_not_implemented` for details.

Three options:
  (a) Add `c0_backextrapolated()` function to `nca/methods.py` and use it in IV NCA
  (b) Accept optional pre-extrapolated t=0 row from the caller
  (c) Leave as-is and mark as unsupported for IV-with-no-t0 data

Recommended: option (a) -- it's in-scope per CLAUDE.md "NCA greenfield moat" and
WNL/PKNCA both implement it. Implementation: log-linear regression on the first
n lambda_z points, extrapolate to t=0, add back-extrapolated trapezoid to AUClast.

---

## What "project complete" looks like

v2.3.0 ships when:
1. Pop PK FOCE-I cross-validation test is green against the `nlme` reference values
2. Covariate skeleton removal is documented as a breaking change
3. conda-forge listing is live

All three are done. v2.3.0 is shipped.

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

Run validation suite only (fast, 172 tests):
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
