"""NONMEM-style population PK dataset loader and validation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass
class PopCSVConfig:
    """Column name mapping for population PK CSV files.

    Parameters
    ----------
    id_col : str
        Subject identifier column. Default ``"ID"``.
    time_col : str
        Nominal time column. Default ``"TIME"``.
    dv_col : str
        Dependent variable (observed concentration) column. Default ``"DV"``.
    pred_col : str
        Population prediction column. Default ``"PRED"``.
    ipred_col : str
        Individual prediction column. Default ``"IPRED"``.
    evid_col : str
        Event ID column. Default ``"EVID"`` (0=obs, 1=dose).
    mdv_col : str
        Missing DV flag column. Default ``"MDV"`` (0=observed, 1=missing).
    """

    id_col: str = "ID"
    time_col: str = "TIME"
    dv_col: str = "DV"
    pred_col: str = "PRED"
    ipred_col: str = "IPRED"
    evid_col: str = "EVID"
    mdv_col: str = "MDV"


_REQUIRED_LOAD_COLS = ("id_col", "time_col", "dv_col")


def load_pop_csv(
    path: str | Path,
    config: PopCSVConfig | None = None,
    *,
    obs_only: bool = True,
) -> pd.DataFrame:
    """Load and validate a population PK dataset from a CSV file.

    Parameters
    ----------
    path : str | Path
        Path to CSV file.
    config : PopCSVConfig | None, optional
        Column name mapping. Defaults to NONMEM standard names.
    obs_only : bool, optional
        If True (default), filter to observation records (EVID==0, MDV==0).

    Returns
    -------
    pd.DataFrame
        Validated DataFrame with at least ID, TIME, DV columns.

    Raises
    ------
    FileNotFoundError
        If the CSV file does not exist.
    ValueError
        If required columns are missing.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Population PK CSV not found: {path}")

    cfg = config or PopCSVConfig()
    df = pd.read_csv(path)

    required = [getattr(cfg, a) for a in _REQUIRED_LOAD_COLS]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"Required columns missing from {path.name}: {missing}. "
            f"Available columns: {list(df.columns)}"
        )

    if obs_only:
        if cfg.evid_col in df.columns:
            df = df[df[cfg.evid_col] == 0].copy()
        if cfg.mdv_col in df.columns:
            df = df[df[cfg.mdv_col] == 0].copy()

    return df.reset_index(drop=True)


def create_nonmem_dataset(
    subject_id: str | int,
    dose_times: list[float],
    dose_amounts: list[float],
    obs_times: list[float],
    obs_dv: list[float],
    *,
    route: str = "oral",
    cmt: int = 1,
) -> pd.DataFrame:
    """Create a NONMEM-compatible single-subject dataset.

    Merges dosing and observation records into a NONMEM-style DataFrame with
    ID, TIME, DV, AMT, EVID, MDV, CMT, ROUTE columns sorted by TIME.

    Parameters
    ----------
    subject_id : str | int
        Subject identifier.
    dose_times : list[float]
        Times of dose administration.
    dose_amounts : list[float]
        Amounts administered at each dose time (must match dose_times length).
    obs_times : list[float]
        Observation time points.
    obs_dv : list[float]
        Observed concentrations at each obs_times (must match obs_times length).
    route : str, optional
        Route of administration string stored in ROUTE column. Default ``"oral"``.
    cmt : int, optional
        Compartment number for dose records. Default 1.

    Returns
    -------
    pd.DataFrame
        NONMEM-compatible dataset sorted by TIME.

    Raises
    ------
    ValueError
        If dose_times and dose_amounts differ in length, or obs_times and obs_dv differ.
    """
    if len(dose_times) != len(dose_amounts):
        raise ValueError(
            f"dose_times length ({len(dose_times)}) != dose_amounts length ({len(dose_amounts)})"
        )
    if len(obs_times) != len(obs_dv):
        raise ValueError(f"obs_times length ({len(obs_times)}) != obs_dv length ({len(obs_dv)})")

    dose_records = pd.DataFrame(
        {
            "ID": subject_id,
            "TIME": dose_times,
            "DV": 0.0,
            "AMT": dose_amounts,
            "EVID": 1,
            "MDV": 1,
            "CMT": cmt,
            "ROUTE": route,
        }
    )

    obs_records = pd.DataFrame(
        {
            "ID": subject_id,
            "TIME": obs_times,
            "DV": obs_dv,
            "AMT": 0.0,
            "EVID": 0,
            "MDV": 0,
            "CMT": cmt,
            "ROUTE": route,
        }
    )

    combined = pd.concat([dose_records, obs_records], ignore_index=True)
    combined = combined.sort_values(["TIME", "EVID"], ascending=[True, False])
    return combined.reset_index(drop=True)
