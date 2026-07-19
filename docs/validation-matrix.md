# Validation Matrix

OpenPKFlow uses executable reference tests to keep scientific claims tied to
checked outputs. This page summarizes the external comparators and the local
test files that support the current validation surface.

Last updated: 2026-07-16

See also [Positioning](positioning.md) and the full test-to-reference map in
[`VALIDATION.md`](https://github.com/priyamthakar/openpkflow/blob/main/VALIDATION.md)
at the repository root.

## External reference checks

| Area | Comparator | Coverage | Test file |
|---|---|---|---|
| NCA, oral theophylline | Phoenix WinNonlin public output | Cmax, Tmax, AUClast, lambda_z, half-life, AUCinf, CL/F, Vz/F across linear and log trapezoid settings | `tests/validation/test_nca_winnonlin_reference.py` |
| NCA, IV bolus indomethacin | Phoenix WinNonlin public output | AUClast, AUCinf, CL, Vz, and C0 back-extrapolation behavior | `tests/validation/test_nca_winnonlin_reference.py` |
| NCA, oral theophylline | PKNCA 0.12.1 | Standard NCA parameter agreement on the bundled theophylline dataset | `tests/validation/test_nca_theoph_reference.py` |
| Steady-state NCA | PKNCA 0.12.1 | Ctau, Cav, Cmax, Cmin, fluctuation, swing, and accumulation-style steady-state parameters | `tests/validation/test_nca_ss_reference.py` |
| NCA | NonCompart 0.8.0 | Cross-checks against an independent R NCA implementation | `tests/validation/test_nca_noncompart_reference.py` |
| Sparse oral model fit | R 4.6.0 `stats::nls` bounded-port fit on `nlme::Theoph` | CL_F, Vz_F, ka, and fitted concentrations for five samples from subject 1 | `tests/validation/test_sparse_nca_theoph_reference.py` |
| Bioequivalence power | PowerTOST 1.5-7 | 2x2 crossover power and sample size; edge cases (GMR at 0.80/1.25 ~ alpha; monotone power in n) | `tests/validation/test_be_power_reference.py` |
| Formal complete balanced 2x2 BE ANOVA | Independent R `aov` / `lm` script | Treatment contrast, GMR, and residual MSE on a pinned complete balanced TR/RT fixture | `tests/validation/test_be_anova_reference.py` |
| Replicate BE screening | R/SAS-compatible scalar fixtures | GMR, CVwR, EMA-style scaled limits, and RSABE point-criterion screening; not full RSABE upper-bound parity | `tests/validation/test_be_replicate_reference.py` |
| Dissolution bootstrap f2 | bootf2 0.4.1 | Bootstrap f2 behavior and confidence interval agreement | `tests/validation/test_dissolution_bootf2_reference.py` |
| Population PK FOCE-I | `nlme` Theophylline reference values from Pinheiro and Bates | Typical-value sanity check for one-compartment oral pop PK estimation | `tests/validation/test_pop_foce_reference.py` |

## Analytical and internal checks

| Area | Validation basis | Test file |
|---|---|---|
| Dissolution model fitting | Known model equations and parameter recovery | `tests/validation/test_dissolution_models_reference.py` |
| IVIVC Level A (WN / LR) | Wagner-Nelson and Loo-Riegelman analytical / R formula references | `tests/validation/test_ivivc_wn_lr_reference.py` |
| IVIVC convolution + Levy | Closed-form zero-order input x 1-cmt UIR; independent fine-grid Riemann convolution; Levy perfect correlation | `tests/validation/test_ivivc_convolution_reference.py` |
| NCA urinary excretion | Reference urinary PK calculations | `tests/validation/test_nca_urine_reference.py` |
| NCA utility math | Bias, RMSE, and percent-tolerance helper behavior | `tests/validation/test_nca_validation.py` |
| PK simulation | Closed-form one- and two-compartment equations | `tests/validation/test_sim_validation.py` |

## Current limits

These tests are designed to catch calculation drift and document agreement with
public comparators. They do not make OpenPKFlow a validated regulated system by
themselves. Regulated use still requires local SOPs, version control, locked
environments, independent review, and study-specific validation.

FDA partial-replicate RSABE is not a validated decision surface yet. The API gate returns
`NOT_EVALUABLE` until external fixtures validate the replicate model and full FDA decision.

## Running validation

Default test runs exclude computationally heavy validation checks marked
`slow`. Run slow validation explicitly before changing population PK estimation
internals:

```bash
python -m pytest -m slow tests/validation -q
```
