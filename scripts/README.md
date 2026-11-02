# scripts

Scripts in this folder are not part of the installed `openpkflow` package.

## Reference Cross-Validation (`crossval/`)

Each script computes reference values outside OpenPKFlow, and a test in
`tests/validation/` pins OpenPKFlow's output to those values. Of the 18 scripts,
10 call an R package (PKNCA, NonCompart, bootf2, disprofas, PowerTOST,
replicateBE or nlmixr2), 6 recompute the formulas in base R, 1 compares against
exported Phoenix WinNonlin results, and 1 rebuilds the Patterson and Jones (2012)
Table II dataset. Run them from the repository root, for example:

```bash
Rscript scripts/crossval/pknca_theoph_crossval.R
```

Scripts that read a dataset default to the CSV under `src/openpkflow/datasets/`
and accept another path as the first argument. Install the R packages a script
loads with `library()` before running it. `VALIDATION.md` maps every validation
test to its reference.

| Script | Reference implementation | Test |
|---|---|---|
| `pknca_theoph_crossval.R`, `pknca_theoph_crossval_extended.R` | PKNCA | `test_nca_theoph_reference.py` |
| `pknca_ss_crossval.R` | PKNCA | `test_nca_ss_reference.py` |
| `pknca_lambda_z_tolerance_crossval.R` | PKNCA | `test_nca_lambda_z_pknca_tolerance.py` |
| `noncompart_theoph_crossval.R` | NonCompart | `test_nca_noncompart_reference.py` |
| `urine_nca_crossval.R` | Base-R urinary NCA formulas on an analytical 1-cmt IV profile | `test_nca_urine_reference.py` |
| `sparse_nca_theoph_crossval.R` | `stats::nls` (port algorithm) | `test_sparse_nca_theoph_reference.py` |
| `crossval_winnonlin.py` | Exported Phoenix WinNonlin results | `test_nca_winnonlin_reference.py` |
| `bootf2_dissolution_crossval.R` | bootf2 | `test_dissolution_bootf2_reference.py` |
| `disprofas_msd_crossval.R` | disprofas | `test_msd_disprofas_reference.py` |
| `dissolution_models_crossval.R` | Base R `lm()` and `optim()` | `test_dissolution_models_reference.py` |
| `ivivc_wn_lr_crossval.R` | Base-R Wagner-Nelson and Loo-Riegelman formulas | `test_ivivc_wn_lr_reference.py` |
| `be_anova_crossval.R` | Base R `lm()` | `test_be_anova_reference.py` |
| `powertost_crossval.R` | PowerTOST | `test_be_power_reference.py` |
| `replicate_be_crossval.R` | Base-R replicate BE summaries; PowerTOST EMA limits if installed | `test_be_replicate_reference.py` |
| `rsabe_patterson2012_crossval.R` | Patterson and Jones (2012), Table II | `test_be_rsabe_reference.py` |
| `rsabe_rds07_identity_check.R` | replicateBE dataset `rds07` | None; prints design counts and geometric means |
| `nlmixr2_popk_crossval.R` | nlmixr2 | None yet; cited by `test_pop_foce_reference.py` until it can run with Rtools |

Test files are in `tests/validation/`.

## Release and Deployment Checks (`ops/`)

- `release_readiness.py`: read-only check run before tagging. It compares the
  `pyproject.toml` version with `__version__`, looks for a matching CHANGELOG
  section, a clean working tree, the local tag and the GitHub release.
- `production_smoke.py`: checks that the hosted API reports the expected version
  in `/health` and `/openapi.json`, and optionally the deployed commit.
  `.github/workflows/production-smoke.yml` runs it.
