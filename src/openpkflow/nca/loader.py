"""NCA data loader: read, validate, and apply BLQ handling to PK concentration data."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

# Regex for string BLQ values like "<0.5" or "< 2.0"
_BLQ_STRING_RE = re.compile(r"^<\s*(\d+\.?\d*)$")

# Canonical BLQ method names
_VALID_BLQ_METHODS = {"none", "drop", "zero", "half_lloq", "lloq"}

# Alias map
_BLQ_ALIASES: dict[str, str] = {
    "m1": "drop",
    "m2": "zero",
}


def load_nca_csv(
    path: str | Path,
    *,
    subject_col: str = "subject",
    time_col: str = "time",
    conc_col: str = "conc",
    dose_col: str = "dose",
    route_col: str = "route",
    lloq: float | None = None,
    blq_col: str | None = None,
    blq_method: str = "none",
) -> pd.DataFrame:
    """Load a PK concentration CSV file with BLQ handling.

    Parameters
    ----------
    path : str or Path
        Path to CSV file.
    subject_col : str, optional
        Column name for subject identifier, by default "subject".
    time_col : str, optional
        Column name for sample time, by default "time".
    conc_col : str, optional
        Column name for observed concentration, by default "conc".
    dose_col : str, optional
        Column name for administered dose, by default "dose".
    route_col : str, optional
        Column name for route of administration, by default "route".
    lloq : float or None, optional
        Lower limit of quantification; required for blq_method "half_lloq" or "lloq".
    blq_col : str or None, optional
        Column name for a pre-existing BLQ indicator (1/True = BLQ).
    blq_method : str, optional
        How to handle BLQ observations. Canonical: "none", "drop", "zero",
        "half_lloq", "lloq". Aliases: "m1" -> "drop", "m2" -> "zero".

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame with canonical column names (subject, time, conc,
        dose, route), sorted by (subject, time) ascending.

    Raises
    ------
    ValueError
        If required columns are missing, blq_method is unknown, or
        blq_method requires lloq but none is provided.
    """
    # --- 1. Normalise BLQ method ---
    normalised_method = _BLQ_ALIASES.get(blq_method, blq_method)
    if normalised_method not in _VALID_BLQ_METHODS:
        raise ValueError(
            f"Unknown blq_method {blq_method!r}. Valid values: "
            f"{sorted(_VALID_BLQ_METHODS)} (aliases: m1->drop, m2->zero)."
        )
    if normalised_method in ("half_lloq", "lloq") and lloq is None:
        raise ValueError(f"blq_method={blq_method!r} requires lloq to be specified (got None).")

    # --- 2. Load CSV as strings to capture "<0.5" patterns ---
    df = pd.read_csv(path, dtype=str)

    # --- 3. Check required columns ---
    required = {subject_col, time_col, conc_col, dose_col, route_col}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Required columns missing from CSV: {sorted(missing)}. "
            f"CSV columns found: {list(df.columns)}."
        )

    # --- 4. Rename to canonical names ---
    rename_map = {
        subject_col: "subject",
        time_col: "time",
        conc_col: "conc",
        dose_col: "dose",
        route_col: "route",
    }
    df = df.rename(columns=rename_map)

    # Validate blq_col exists if specified
    if blq_col is not None and blq_col not in df.columns:
        raise ValueError(f"blq_col={blq_col!r} not found in CSV columns: {list(df.columns)}.")

    # --- 5. Parse numeric types for non-conc columns ---
    df["time"] = pd.to_numeric(df["time"], errors="coerce").astype(float)
    df["dose"] = pd.to_numeric(df["dose"], errors="coerce").astype(float)

    # --- 6. String-BLQ parsing on the conc column ---
    # Scan for "<value" patterns; mark those rows as BLQ before other handling.
    string_blq_mask = pd.Series(False, index=df.index)
    parsed_conc: list[float] = []

    for val in df["conc"]:
        m = _BLQ_STRING_RE.match(str(val).strip())
        if m:
            parsed_conc.append(float(m.group(1)))
        else:
            try:
                parsed_conc.append(float(val))
            except (ValueError, TypeError):
                parsed_conc.append(float("nan"))

    # Rebuild the string_blq_mask using the original raw column
    raw_conc = df["conc"].copy()
    for idx, val in raw_conc.items():
        if _BLQ_STRING_RE.match(str(val).strip()):
            string_blq_mask.loc[idx] = True

    df["conc"] = pd.array(parsed_conc, dtype=float)

    # --- 7. Combine BLQ flags ---
    combined_blq_mask = string_blq_mask.copy()
    if blq_col is not None:
        col_blq = df[blq_col].astype(str).str.strip().isin({"1", "True", "true", "1.0"})
        combined_blq_mask = combined_blq_mask | col_blq

    # NaN rows that are NOT from string-BLQ parsing (failed numeric parse)
    nan_mask = df["conc"].isna() & ~string_blq_mask

    # --- 8. Apply BLQ method (fail-closed for string/flagged BLQ) ---
    if normalised_method == "none":
        # Strings like "<0.5" must not silently become observed 0.5.
        if bool(combined_blq_mask.any()):
            n_blq = int(combined_blq_mask.sum())
            raise ValueError(
                f"Found {n_blq} BLQ observation(s) (string markers such as '<0.5' "
                "and/or blq_col flags) but blq_method='none'. Choose an explicit "
                "BLQ method: 'drop', 'zero', 'half_lloq', or 'lloq'."
            )
        # Unparseable non-BLQ NaNs are also rejected under fail-closed loading.
        if bool(nan_mask.any()):
            n_nan = int(nan_mask.sum())
            raise ValueError(
                f"Found {n_nan} non-numeric concentration value(s) that are not "
                "BLQ markers. Fix the input or use blq_method='drop'."
            )

    elif normalised_method == "drop":
        drop_mask = combined_blq_mask | nan_mask
        df = df[~drop_mask].copy()

    elif normalised_method == "zero":
        df.loc[combined_blq_mask, "conc"] = 0.0

    elif normalised_method == "half_lloq":
        assert lloq is not None  # already validated above
        # Prefer explicit LLOQ; fall back to parsed "<x" threshold per row.
        for idx in df.index[combined_blq_mask]:
            df.loc[idx, "conc"] = float(lloq) * 0.5

    elif normalised_method == "lloq":
        assert lloq is not None
        df.loc[combined_blq_mask, "conc"] = float(lloq)

    else:
        raise ValueError(f"Unknown blq_method after normalisation: {normalised_method!r}.")

    # --- 9. Final type coercion ---
    df["conc"] = df["conc"].astype(float)

    # --- 10. Sort by (subject, time) ---
    df = df.sort_values(["subject", "time"]).reset_index(drop=True)

    return df
