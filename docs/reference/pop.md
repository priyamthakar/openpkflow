# openpkflow.pop

Population PK diagnostics: GOF plots, simulation-based VPC, NONMEM-style dataset helpers.

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

## GOF panels (4-panel figure)

1. OBS vs PRED
2. OBS vs IPRED
3. IWRES vs TIME
4. IWRES vs IPRED

All panels at 600 DPI (print quality).

## Notes

- `simulate_vpc` uses `openpkflow.sim.simulate()` under the hood with proportional + additive residual noise.
- IWRES uses a proportional error model: IWRES = (OBS - IPRED) / (sigma * IPRED).
- Population estimation (SAEM/FOCE) is not included in v1.0.0 and is planned for v1.1.0.
