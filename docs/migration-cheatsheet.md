# Coming from WinNonlin / NONMEM

A quick-reference guide for scientists transitioning from Phoenix WinNonlin and NONMEM to OpenPKFlow.

---

## WinNonlin NCA -> OpenPKFlow NCA

| WinNonlin | OpenPKFlow | Notes |
|-----------|-----------|-------|
| `NCA -> Model 200 (plasma)` | `NCAStudy.from_csv()` + `study.analyze()` | CSV input, returns `NCASummaryResults` |
| `AUClast (linear trapezoidal)` | `auc_linear(times, concs)` | Explicit method required |
| `AUClast (log-linear trapezoidal)` | `auc_log(times, concs)` | Returns `AUCResult` with warnings |
| `AUC linear-up/log-down` | `auc_linear_up_log_down(times, concs)` | FDA/EMA default |
| `AUCINF_obs` | `NCAResult.auc_inf_obs` | `AUClast + Clast/lambda_z` |
| `%AUCextrap` | `NCAResult.auc_percent_extrapolated` | Warns if >20% (FDA criterion) |
| `Cmax` | `cmax(concs)` | `NCAResult.cmax` |
| `Tmax` | `tmax(times, concs)` | `NCAResult.tmax` |
| `lambda_z` (best-fit) | `lambda_z(times, concs, method="auto")` | BAR² auto-selects tail window |
| `t1/2` | `NCAResult.half_life` | `ln(2) / lambda_z` |
| `CL_F` (oral) | `NCAResult.cl_f` | Apparent clearance |
| `Vz_F` (oral) | `NCAResult.vz_f` | Apparent volume |
| `CL` (IV) | `NCAResult.cl` | Absolute clearance |
| BLQ handling (set to 0) | `blq_method="zero"` | One of: none/drop/zero/half_lloq/lloq |
| Steady-state NCA | `NCAStudy(..., steady_state=True, tau=12)` | AUCtau, Cmax_ss, Cmin_ss, fluctuation% |
| Urinary excretion | `NCAStudy(..., urine_volume_col="vol", urine_conc_col="conc_u")` | Ae, CLr, %excreted |
| CDISC PP output | `summary.to_cdisc_pp()` | PPTESTCD/PPORRES/PPORRESU format |
| Dose-normalised params | `NCAResult.dn_auclast`, `.dn_cmax` | Per-mg normalisation |
| C0 back-extrapolation (IV bolus) | `c0_back_extrapolated(times, concs)` | OLS log-linear on first 2 points; prepend t=0, C0 to profile |
| Sparse oral PK (model-informed) | `fit_sparse_1cmt_oral()` | One-compartment oral screening from 3+ samples; not a replacement for standard NCA |

### Example

```python
from openpkflow.nca import NCAStudy

study = NCAStudy.from_csv("subjects.csv", auc_method="linear_up_log_down")
results = study.analyze()
print(results.summary())
results.report("nca_report.html")
```

---

## WinNonlin Bioequivalence -> OpenPKFlow BE

| WinNonlin | OpenPKFlow | Notes |
|-----------|-----------|-------|
| `BE -> 2x2 crossover (TOST)` | `be_tost(reference, test)` | Paired per-subject log-differences |
| GMR + 90% CI | `BETOSTResult.gmr`, `.gmr_lower_90ci`, `.gmr_upper_90ci` | Default limits 80-125% |
| Intra-subject CV% | `BETOSTResult.cv_intra_pct` | Back-transformed from log-diff SD |
| BE verdict (PASS/FAIL) | `BETOSTResult.bioequivalent` | Boolean flag |
| NTI limits (90-111%) | `be_tost(..., be_lower=0.90, be_upper=1.1111)` | |
| Sample size (power 80%) | `be_sample_size(gmr=0.95, cv=0.20)` | Sequential search |
| Power for given N | `be_tost_power(gmr=0.95, cv=0.20, n=24)` | Non-central t exact method |
| BE report | `result.report("be_report.html")` | HTML with CI bar chart |
| Formal complete balanced 2x2 ANOVA | `formal_be_anova(long_data, parameter="AUCinf")` | Requires complete balanced TR/RT long-format data |

---

## WinNonlin IVIVC -> OpenPKFlow IVIVC

| WinNonlin | OpenPKFlow | Notes |
|-----------|-----------|-------|
| Wagner-Nelson deconvolution | `wagner_nelson(times, concs)` | Returns F_a fraction absorbed |
| Loo-Riegelman deconvolution | `loo_riegelman(times, concs, dose, k10, k12, k21)` | 2-compartment method |
| Convolution prediction | `convolution_predict(diss_times, diss_frac, ir_fn)` | Numerical convolution |
| Levy plot | `levy_plot_data(f_in_vitro, f_in_vivo)` | Linear regression R² |
| Predictability (%PE) | `ivivc_predictability(...)` | FDA <=15% individual, <=10% mean |

### Example

```python
from openpkflow.ivivc import IVIVCStudy

study = IVIVCStudy(dissolution_csv="dissolution.csv", plasma_csv="plasma.csv",
                   dose=100, method="wagner_nelson")
result = study.run()
result.report("ivivc_report.html")
```

---

## Phoenix NLME / NONMEM -> OpenPKFlow Pop PK

| Phoenix NLME / NONMEM | OpenPKFlow | Notes |
|----------------------|-----------|-------|
| FOCE-I (METHOD=1) | `run_foce_i(model, data)` | scipy L-BFGS-B, zero extra deps |
| SAEM (METHOD=3) | `run_saem(model, data, n_iterations=500)` | PyMC optional, numpy fallback; chain mean estimates |
| `$PK` block | `PopPKModel(route="oral", n_cmt=1, omega_type="diagonal")` | Frozen dataclass |
| `$THETA` | `model.to_theta()`/`model.from_theta()` | Pack/unpack for optimizer |
| `$OMEGA` | `PopPKModel(omega_type="full")` | Diagonal or full block matrix |
| `$SIGMA` | Built into proportional error model | Fixed at v2.3.0 |
| `$DATA` | `load_pop_csv(path)` | NONMEM-style CSV (ID, TIME, DV, EVID, MDV) |
| `$TABLE` output | `result.to_dataframe()` | Parameter estimates + SEs |
| Objective function (-2LL) | `PopPKResult.minus_2ll` | Also AIC, BIC |
| EBE shrinkage | `PopPKResult.ebe_shrinkage` | Per-parameter shrinkage |
| SEs (delta method) | `PopPKResult.se_*` fields | Via inverse Hessian |
| 2-compartment models | `PopPKModel(n_cmt=2)` | Oral or IV bolus |
| IV bolus route | `PopPKModel(route="iv_bolus")` | Supports 1-cmt and 2-cmt |
| Covariates | Not available (removed in v2.3.0) | Use Pharmpy/nlmixr2 for covariate selection |
| GOF diagnostic plots | `result.plot()` | 6-panel OBS/IPRED/CWRES/EBE |
| VPC | `simulate_vpc(model, data)` | Simulation-based percentile bands |
| Population dataset | `create_nonmem_dataset(...)` | Dose + observation records merged |

### Example

```python
from openpkflow.pop import PopPKModel, run_foce_i

model = PopPKModel(route="oral", n_cmt=1, omega_type="diagonal")
result = run_foce_i(model, "theoph.csv")
print(result.summary())
result.report("pop_report.html")
```

---

## NONMEM VPC -> OpenPKFlow Pop Diagnostics

| NONMEM (PsN `vpc`) | OpenPKFlow | Notes |
|-------------------|-----------|-------|
| Simulation-based VPC | `simulate_vpc(model, data, n_sim=500)` | Users `sim/` analytical engine |
| 5th/50th/95th percentile bands | `VPCResult.observed_bands`, `.simulated_bands` | Time-binned |
| VPC plot | `vpc_result.plot()` or `vpc_result.report()` | scatter + band overlay |

---

## WinNonlin Dissolution -> OpenPKFlow Dissolution

| WinNonlin | OpenPKFlow | Notes |
|-----------|-----------|-------|
| f1 (difference factor) | `f1(reference, test)` | 0 = identical |
| f2 (similarity factor) | `f2(reference, test)` | 100 = identical, >=50 passes |
| Bootstrap f2 | `study.bootstrap_compare(ref, test)` | CI for samples <12 vessels |
| Max deviation | `max_deviation(reference, test)` | FDA alternative when f2 cannot be used |
| MSD (Mahalanobis) | `msd(reference, test_matrix)` | Chi-squared test |
| Model fitting (Weibull) | `study.fit_models(formulation, models=["weibull"])` | AICc ranking |
| Model fitting (KP) | `models=["korsmeyer_peppas"]` | 60% rule check |
| Model fitting (Higuchi) | `models=["higuchi"]` | |
| Multi-media (pH panel) | `MultiMediaStudy({...})` | ICH M13A/B |
| Alcohol dose-dumping | Supported in multi-media | Separate medium with ethanol |
| Report generation | `result.report("out.html")` | HTML/PDF/DOCX/MD |

### Example

```python
from openpkflow.dissolution import DissolutionStudy

study = DissolutionStudy.from_csv("dissolution.csv")
result = study.compare("Reference", "Test")
print(f"f2 = {result.f2_value:.1f}")  # >= 50: similar
result.report("dissolution_report.html")
```

---

## PK Simulation -> OpenPKFlow Sim

| Phoenix WinNonlin PKS | OpenPKFlow | Notes |
|----------------------|-----------|-------|
| 1-cmt IV bolus | `c_1cmt_iv_bolus(times, dose, CL, Vz)` | Gibaldi & Perrier 2nd ed. |
| 1-cmt IV infusion | `c_1cmt_iv_infusion(times, dose, CL, Vz, duration)` | Constant-rate infusion |
| 1-cmt oral | `c_1cmt_oral(times, dose, CL_F, Vz_F, ka)` | Bateman equation |
| 2-cmt IV bolus | `c_2cmt_iv_bolus(times, dose, CL, V1, Q, V2)` | Biexponential |
| 2-cmt oral | `c_2cmt_oral(times, dose, CL_F, Vz_F, ka, Q, V2)` | 3-exponential |
| Repeated dosing | `DoseRegimen.from_repeated(...)` + `simulate()` | Superposition |
| Model object | `OneCompartmentModel(...)` or `TwoCompartmentModel(...)` | CL/V parameterization |

---

## Key Differences

**Parameterization:** OpenPKFlow uses CL/V (or CL_F/Vz_F), not rate constants (k10, k12, k21). Clearance and volume are more interpretable and align with NCA output naming.

**No GUI:** OpenPKFlow is a Python library + CLI. All outputs are scriptable, versionable, and CI-compatible.

**No covariates in Pop PK:** Covariate estimation code was removed in v2.3.0. Use Pharmpy or nlmixr2 for covariate selection, then OpenPKFlow for base model estimation.

**Reports are static HTML/PDF/DOCX/MD:** No interactive dashboards. All report templates are Jinja2 and can be customized.

**RSABE / replicate BE:** OpenPKFlow retains research-grade replicate screening. FDA
partial-replicate RSABE is currently a fail-closed `NOT_EVALUABLE` validation gate;
EMA ABEL and full-replicate RSABE are not supported.

---

## Environment R -> OpenPKFlow

| R (PKNCA/nlmixr2) | OpenPKFlow | Notes |
|------------------|-----------|-------|
| `PKNCA::pk.nca()` | `NCAStudy.from_csv().analyze()` | Cross-validated against PKNCA 0.12.1 |
| `nlmixr2::nlmixr()` FOCE-I | `run_foce_i()` | Cross-validated against nlme (Pinheiro & Bates 2000, Table 8.1) |
| `nlmixr2::nlmixr()` SAEM | `run_saem()` | PyMC Metropolis + Robbins-Monro |
| `PowerTOST::power.TOST()` | `be_tost_power()` | Exact non-central t method |
| `PowerTOST::sampleN.TOST()` | `be_sample_size()` | Cross-validated against PowerTOST 1.5-7 |
| `bootf2::calcf2()` | `f2(method="all_points")` | Point estimate validated |
| `lm()` / `optim()` model fits | `fit_dissolution_models()` | All 5 models cross-validated against base R |
