"""CSV and Excel loaders for dissolution data."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from pydantic import BaseModel


class DissolutionCSVConfig(BaseModel):
    """Column name configuration for dissolution CSV/Excel files."""

    formulation_col: str = "formulation"
    batch_col: str = "batch"
    time_col: str = "time"
    percent_released_col: str = "percent_released"


def _validate_dissolution_df(
    df: pd.DataFrame,
    cfg: DissolutionCSVConfig,
    source_name: str,
) -> pd.DataFrame:
    """Validate a raw dissolution DataFrame and return a standardized copy.

    Parameters
    ----------
    df : pd.DataFrame
        Raw DataFrame loaded from CSV or Excel.
    cfg : DissolutionCSVConfig
        Column name configuration.
    source_name : str
        File name used in error messages.

    Returns
    -------
    pd.DataFrame
        Standardized DataFrame with columns: formulation, batch, time, percent_released.

    Raises
    ------
    ValueError
        If required columns are missing or data fails validation.
    """
    required = {cfg.formulation_col, cfg.batch_col, cfg.time_col, cfg.percent_released_col}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Required columns missing from '{source_name}': {sorted(missing)}")

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

    df = df.copy()
    df[time_col] = pd.to_numeric(df[time_col], errors="coerce")
    if df[time_col].isna().any():
        raise ValueError(f"Column '{time_col}' contains non-numeric values. Time must be numeric.")
    if not np.isfinite(df[time_col].to_numpy(dtype=float)).all():
        raise ValueError(f"Column '{time_col}' contains non-finite values.")
    if (df[time_col] < 0).any():
        raise ValueError(
            f"Column '{time_col}' contains negative values. Time must be non-negative."
        )

    df[pct_col] = pd.to_numeric(df[pct_col], errors="coerce")
    if df[pct_col].isna().any():
        raise ValueError(
            f"Column '{pct_col}' contains non-numeric values. Percent released must be numeric."
        )
    if not np.isfinite(df[pct_col].to_numpy(dtype=float)).all():
        raise ValueError(f"Column '{pct_col}' contains non-finite values.")
    out_of_range = df[(df[pct_col] < 0) | (df[pct_col] > 100)]
    if not out_of_range.empty:
        bad_vals = out_of_range[pct_col].tolist()
        raise ValueError(f"Column '{pct_col}' contains values outside [0, 100]: {bad_vals}")

    formulations = df[form_col].unique()
    empty_formulations = [str(f) for f in formulations if df[df[form_col] == f].shape[0] == 0]
    if empty_formulations:
        raise ValueError(f"The following formulations have no rows: {empty_formulations}")

    return pd.DataFrame(
        {
            "formulation": df[form_col].astype(str),
            "batch": df[batch_col].astype(str),
            "time": df[time_col].astype(float),
            "percent_released": df[pct_col].astype(float),
        }
    )


def validate_dissolution_dataframe(
    df: pd.DataFrame,
    config: DissolutionCSVConfig | None = None,
    *,
    source_name: str = "dataframe",
) -> pd.DataFrame:
    """Validate in-memory dissolution data and return standardized columns.

    Parameters
    ----------
    df : pd.DataFrame
        Raw in-memory dissolution data.
    config : DissolutionCSVConfig | None, optional
        Column name configuration. Uses defaults if omitted.
    source_name : str, optional
        Source label used in validation errors.

    Returns
    -------
    pd.DataFrame
        Validated copy with canonical dissolution column names.

    Raises
    ------
    ValueError
        If required data are missing, non-finite, or outside supported ranges.
    """
    return _validate_dissolution_df(df, config or DissolutionCSVConfig(), source_name)


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
    return _validate_dissolution_df(df, cfg, path.name)


def load_dissolution_excel(
    path: str | Path,
    config: DissolutionCSVConfig | None = None,
    sheet_name: str | int = 0,
) -> pd.DataFrame:
    """Load and validate a dissolution Excel file (.xlsx or .xls).

    Requires ``openpyxl`` (included in ``pip install openpkflow[reports]``).

    Parameters
    ----------
    path : str | Path
        Path to Excel file (.xlsx or .xls).
    config : DissolutionCSVConfig | None, optional
        Column name configuration. Uses defaults if None.
    sheet_name : str or int, optional
        Sheet name or zero-based index. Defaults to the first sheet (0).

    Returns
    -------
    pd.DataFrame
        Validated DataFrame with standardized columns: formulation (str),
        batch (str), time (float), percent_released (float).

    Raises
    ------
    FileNotFoundError
        If path does not exist.
    ImportError
        If openpyxl is not installed.
    ValueError
        If required columns are missing or data fails validation.
    """
    try:
        import openpyxl  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "openpyxl is required to read Excel files. "
            "Install it with: pip install openpkflow[reports]"
        ) from exc

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Dissolution Excel file not found: {path}")

    cfg = config or DissolutionCSVConfig()
    df = pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl")
    return _validate_dissolution_df(df, cfg, path.name)


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
    means = subset.groupby(time_col, sort=True)[pct_col].mean().reset_index()
    time_points = means[time_col].tolist()
    mean_pct = means[pct_col].tolist()
    return time_points, mean_pct
