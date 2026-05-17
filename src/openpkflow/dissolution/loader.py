"""CSV loader for dissolution data."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from pydantic import BaseModel


class DissolutionCSVConfig(BaseModel):
    """Column name configuration for dissolution CSV files."""

    formulation_col: str = "formulation"
    batch_col: str = "batch"
    time_col: str = "time"
    percent_released_col: str = "percent_released"


def load_dissolution_csv(
    path: str | Path,
    config: DissolutionCSVConfig | None = None,
) -> pd.DataFrame:
    """Load and validate a dissolution CSV file.

    Parameters
    ----------
    path : str | Path
        Path to CSV file.
    config : DissolutionCSVConfig | None, optional
        Column name configuration. Uses defaults if None.

    Returns
    -------
    pd.DataFrame
        Validated DataFrame with standardized columns: formulation (str),
        batch (str), time (float), percent_released (float).

    Raises
    ------
    FileNotFoundError
        If path does not exist.
    ValueError
        If required columns are missing or data fails validation.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Dissolution CSV not found: {path}")

    cfg = config or DissolutionCSVConfig()

    df = pd.read_csv(path)

    required = {
        cfg.formulation_col,
        cfg.batch_col,
        cfg.time_col,
        cfg.percent_released_col,
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Required columns missing from '{path.name}': {sorted(missing)}"
        )

    form_col = cfg.formulation_col
    batch_col = cfg.batch_col
    time_col = cfg.time_col
    pct_col = cfg.percent_released_col

    for col in [form_col, batch_col, time_col, pct_col]:
        n_null = df[col].isna().sum()
        if n_null > 0:
            raise ValueError(
                f"Column '{col}' contains {n_null} NaN value(s). "
                "All required columns must be complete."
            )

    df[time_col] = pd.to_numeric(df[time_col], errors="coerce")
    if df[time_col].isna().any():
        raise ValueError(
            f"Column '{time_col}' contains non-numeric values. "
            "Time must be numeric."
        )
    if (df[time_col] < 0).any():
        raise ValueError(
            f"Column '{time_col}' contains negative values. "
            "Time must be non-negative."
        )

    df[pct_col] = pd.to_numeric(df[pct_col], errors="coerce")
    if df[pct_col].isna().any():
        raise ValueError(
            f"Column '{pct_col}' contains non-numeric values. "
            "Percent released must be numeric."
        )
    out_of_range = df[(df[pct_col] < 0) | (df[pct_col] > 100)]
    if not out_of_range.empty:
        bad_vals = out_of_range[pct_col].tolist()
        raise ValueError(
            f"Column '{pct_col}' contains values outside [0, 100]: {bad_vals}"
        )

    formulations = df[form_col].unique()
    empty_formulations = [
        str(f) for f in formulations if df[df[form_col] == f].shape[0] == 0
    ]
    if empty_formulations:
        raise ValueError(
            f"The following formulations have no rows: {empty_formulations}"
        )

    result = pd.DataFrame(
        {
            "formulation": df[form_col].astype(str),
            "batch": df[batch_col].astype(str),
            "time": df[time_col].astype(float),
            "percent_released": df[pct_col].astype(float),
        }
    )
    return result


def get_formulation_means(
    df: pd.DataFrame,
    formulation: str,
    time_col: str = "time",
    pct_col: str = "percent_released",
    formulation_col: str = "formulation",
) -> tuple[list[float], list[float]]:
    """Return mean dissolution profile for a given formulation, averaged across batches.

    Parameters
    ----------
    df : pd.DataFrame
        Dissolution DataFrame (as returned by load_dissolution_csv).
    formulation : str
        Formulation label to filter on.
    time_col : str, optional
        Name of the time column. Defaults to "time".
    pct_col : str, optional
        Name of the percent released column. Defaults to "percent_released".
    formulation_col : str, optional
        Name of the formulation column. Defaults to "formulation".

    Returns
    -------
    tuple[list[float], list[float]]
        A tuple of (time_points, mean_percent_released), each sorted by time.
    """
    subset = df[df[formulation_col] == formulation]
    means = (
        subset.groupby(time_col, sort=True)[pct_col]
        .mean()
        .reset_index()
    )
    time_points = means[time_col].tolist()
    mean_pct = means[pct_col].tolist()
    return time_points, mean_pct
