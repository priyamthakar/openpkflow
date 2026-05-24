# openpkflow.pop

Population PK diagnostics and research-grade estimation helpers.

## Public API

| Symbol | Type | Description |
|--------|------|-------------|
| `GOFResult` | dataclass | GOF analysis result; `.summary()`, `.plot()`, `.report()` |
| `compute_iwres(obs, ipred, sigma)` | function | Individual weighted residuals (proportional error) |
| `obs_pred_metrics(obs, pred)` | function | MPE, RMSE, rRMSE, R2 |
| `VPCResult` | dataclass | VPC result; `.report()` |
| `simulate_vpc(obs_df, model, n_sims, seed)` | function | Simulation-based VPC |
| `load_pop_csv(path, config)` | function | NONMEM-style CSV loader (EVID/MDV filtering) |
| `PopCSVConfig` | dataclass | CSV column config |
| `create_nonmem_dataset(obs_df, dose_df)` | function | Merge obs + doses into NONMEM-compatible DataFrame |
| `PopPKModel` | dataclass | FOCE-I/SAEM model definition for 1- and 2-compartment oral/IV bolus models |
| `PopPKResult` | dataclass | Population estimation result; `.summary()`, `.plot()`, `.report()` |
| `run_foce_i(df, model)` | function | FOCE-I estimation using scipy |
| `run_saem(df, model)` | function | SAEM estimation using the `[bayes]` extra when available |

## GOF panels (4-panel figure)

1. OBS vs PRED
2. OBS vs IPRED
3. IWRES vs TIME
4. IWRES vs IPRED

All panels at 600 DPI (print quality).

## Notes

- `simulate_vpc` uses `openpkflow.sim.simulate()` under the hood with proportional + additive residual noise.
- IWRES uses a proportional error model: IWRES = (OBS - IPRED) / (sigma * IPRED).
- FOCE-I and SAEM are research-grade helpers. FOCE-I typical values are sanity-checked
  against the `nlme` Theophylline reference in `tests/validation/test_pop_foce_reference.py`.
- Covariate modeling was removed in v2.3.0 because the v2.2.0 API was a non-functional
  skeleton that did not affect estimation.
