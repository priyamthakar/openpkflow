"""Probe script: run openpkflow FOCE-I on theoph.csv and print parameters.

Usage (from project root):
    python scripts/probe_foce_i.py
"""

from __future__ import annotations

import pandas as pd

from openpkflow.datasets import example_theoph_path
from openpkflow.pop.estimation import PopPKModel, run_foce_i


def build_nm_dataset(theoph_csv: str) -> pd.DataFrame:
    """Convert theoph.csv to NONMEM-style dataset with EVID, AMT, DV, TIME, ID."""
    raw = pd.read_csv(theoph_csv)

    # Build dosing rows at TIME=0 for each subject
    dose_rows = []
    for subj, grp in raw.groupby("subject"):
        dose = float(grp["dose"].iloc[0])
        dose_rows.append(
            {
                "ID": str(subj),
                "TIME": 0.0,
                "AMT": dose,
                "DV": 0.0,
                "EVID": 1,
            }
        )

    # Build observation rows (TIME > 0 only — exclude pre-dose 0-time obs)
    obs_rows = []
    for _, row in raw.iterrows():
        if row["time"] > 0:
            obs_rows.append(
                {
                    "ID": str(int(row["subject"])),
                    "TIME": float(row["time"]),
                    "AMT": 0.0,
                    "DV": float(row["conc"]),
                    "EVID": 0,
                }
            )

    df = pd.DataFrame(dose_rows + obs_rows)
    df = df.sort_values(["ID", "TIME", "EVID"], ascending=[True, True, False])
    df = df.reset_index(drop=True)
    return df


def main() -> None:
    csv_path = example_theoph_path()
    print(f"Dataset: {csv_path}")

    df = build_nm_dataset(csv_path)
    print(f"Subjects: {df['ID'].nunique()}, Rows: {len(df)}, Obs: {(df['EVID'] == 0).sum()}")

    model = PopPKModel(
        route="oral",
        fixed_effects={"CL_F": 3.0, "Vz_F": 30.0, "ka": 1.5},
        omega_diag={"CL_F": 0.1, "Vz_F": 0.1, "ka": 0.1},
        sigma_prop=0.15,
        sigma_add=0.1,
    )

    print("Running FOCE-I (this may take 1-3 min)...")
    result = run_foce_i(df, model)

    print("\n" + "=" * 60)
    print("FOCE-I Results")
    print("=" * 60)
    print(result.summary())

    print("\n# Python dict for test_pop_foce_reference.py:")
    print("_FOCE_I_REFERENCE = {")
    for k, v in result.theta_pop.items():
        print(f'    "CL_F" if k == "CL_F" else k: {v:.6f},', end="")
        print(f"  # {k}")
    print("")
    for k, v in result.theta_pop.items():
        print(f'    "{k}": {v:.6f},')
    print("")
    for k, v in result.omega_diag.items():
        print(f'    "omega_{k}": {v:.6f},')
    print(f'    "sigma_prop": {result.sigma_prop:.6f},')
    print(f'    "sigma_add":  {result.sigma_add:.6f},')
    print("}")

    print(f"\n# -2LL = {result.minus2ll:.4f}")
    print(f"# AIC  = {result.aic:.4f}")
    print(f"# BIC  = {result.bic:.4f}")
    print(f"# Converged: {result.converged}")
    if result.warnings:
        print("# Warnings:")
        for w in result.warnings:
            print(f"#   {w}")


if __name__ == "__main__":
    main()
