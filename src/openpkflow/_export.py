"""Shared conversion of result objects to plain Python data."""

from __future__ import annotations

import dataclasses
from typing import Any

import numpy as np
import pandas as pd


def to_builtin(value: Any) -> Any:
    """Convert a result value to JSON-compatible built-in Python types.

    Parameters
    ----------
    value : Any
        Dataclass, NumPy array or scalar, pandas object, mapping, sequence or scalar.

    Returns
    -------
    Any
        The same data as dicts, lists, str, int, float, bool or None. NaN stays
        a float, as in the existing ``to_dict()`` methods.
    """
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return dataclass_to_dict(value)
    if isinstance(value, pd.DataFrame):
        return [to_builtin(row) for row in value.to_dict(orient="records")]
    if isinstance(value, pd.Series):
        return to_builtin(value.tolist())
    if isinstance(value, np.ndarray):
        return to_builtin(value.tolist())
    if isinstance(value, np.generic):
        return to_builtin(value.item())
    if isinstance(value, dict):
        return {_key(k): to_builtin(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [to_builtin(v) for v in value]
    return value


def dataclass_to_dict(obj: Any, exclude: tuple[str, ...] = ()) -> dict[str, Any]:
    """Convert a dataclass instance to a dict of built-in types.

    Parameters
    ----------
    obj : Any
        Dataclass instance.
    exclude : tuple[str, ...]
        Field names to leave out. Fields whose names start with ``_`` are always
        left out.

    Returns
    -------
    dict[str, Any]
        Field name to converted value.
    """
    return {
        f.name: to_builtin(getattr(obj, f.name))
        for f in dataclasses.fields(obj)
        if not f.name.startswith("_") and f.name not in exclude
    }


def _key(key: Any) -> Any:
    if isinstance(key, np.generic):
        key = key.item()
    return key if isinstance(key, str | int | float | bool) or key is None else str(key)
