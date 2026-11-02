# scripts

Helper scripts that are not part of the installed `openpkflow` package.

## `crossval/` - reference cross-validation

Each script recomputes reference values with an independent implementation
(mostly R packages) so that `tests/validation/` can pin OpenPKFlow against them.
Run them from the repository root, for example:

```bash
Rscript scripts/crossval/pknca_theoph_crossval.R
```

Scripts that read a dataset default to the CSV under `src/openpkflow/datasets/`
and also accept a path as the first argument. Install the R packages each script
loads before running it. See `VALIDATION.md` for the full test-to-reference map.

| Script | Reference | Pinned by |
|---|---|---|
| `pknca_theoph_crossval.R`, `pknca_theoph_crossval_extended.R` | PKNCA | `tests/validation/test_nca_theoph_reference.py` |
| `pknca_ss_crossval.R` | PKNCA | `tests/validation/test_nca_ss_reference.py` |
| `pknca_lambda_z_tolerance_crossval.R` | PKNCA | `tests/validation/test_nca_lambda_z_pknca_tolerance.py` |
| `noncompart_theoph_crossval.R` | NonCompart | `tests/validation/test_nca_noncompart_reference.py` |
| `urine_nca_crossval.R` | independent base-R formulas (analytical 1-cmt IV) | `tests/validation/test_nca_urine_reference.py` |
| `sparse_nca_theoph_crossval.R` | `stats::nls` | `tests/validation/test_sparse_nca_theoph_reference.py` |
| `crossval_winnonlin.py` | Phoenix WinNonlin public outputs | `tests/validation/test_nca_winnonlin_reference.py` |
| `bootf2_dissolution_crossval.R` | bootf2 | `tests/validation/test_dissolution_bootf2_reference.py` |
| `disprofas_msd_crossval.R` | disprofas | `tests/validation/test_msd_disprofas_reference.py` |
| `dissolution_models_crossval.R` | base R `lm()` / `optim()` | `tests/validation/test_dissolution_models_reference.py` |
| `ivivc_wn_lr_crossval.R` | independent base-R Wagner-Nelson / Loo-Riegelman | `tests/validation/test_ivivc_wn_lr_reference.py` |
| `be_anova_crossval.R` | base R `lm()` | `tests/validation/test_be_anova_reference.py` |
| `powertost_crossval.R` | PowerTOST | `tests/validation/test_be_power_reference.py` |
| `replicate_be_crossval.R` | replicateBE | `tests/validation/test_be_replicate_reference.py` |
| `rsabe_patterson2012_crossval.R` | Patterson & Jones (2012), Table II | `tests/validation/test_be_rsabe_reference.py` |
| `rsabe_rds07_identity_check.R` | replicateBE `rds07` | exploratory design/GMR check |
| `nlmixr2_popk_crossval.R` | nlmixr2 | `tests/validation/test_pop_foce_reference.py` (waiting on an R toolchain) |

## `ops/` - release and deployment checks

- `release_readiness.py` - read-only pre-tag metadata and release-state checks.
- `production_smoke.py` - verifies the hosted API version and commit; run by
  `.github/workflows/production-smoke.yml`.
