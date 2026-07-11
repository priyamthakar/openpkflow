"""SUPAC-IR change-level screening and alcohol dose-dumping helpers.

Transparent screening utilities based on FDA SUPAC-IR (1995) excipient-function
tables. These helpers do NOT replace a full SUPAC guidance interpretation,
regulatory filing strategy, or qualified CMC judgement.

References
----------
FDA Guidance for Industry: Immediate Release Solid Oral Dosage Forms:
Scale-Up and Postapproval Changes (SUPAC-IR, 1995). CDER.

FDA Guidance for Industry: Dissolution Testing of Immediate Release Solid
Oral Dosage Forms (1997). CDER.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from openpkflow.dissolution.similarity import f2

# Excipient functional classes from SUPAC-IR composition tables (percent of
# total target dosage-form weight). Level 1 max and Level 2 max absolute %.
ComponentCategory = Literal[
    "filler",
    "binder",
    "disintegrant_starch",
    "disintegrant_other",
    "lubricant_stearate",
    "lubricant_other",
    "glidant",
    "film_coat",
    # Deprecated collapsed aliases (map to nearest function-specific class)
    "non_critical",
    "critical",
]

SupacLevel = Literal[1, 2, 3]

# Absolute percent change of total formulation weight (SUPAC-IR 1995 tables).
# L1: change_pct <= l1_max; L2: l1_max < change_pct <= l2_max; else L3.
_THRESHOLDS: dict[str, tuple[float, float]] = {
    "filler": (5.0, 10.0),
    "binder": (0.5, 1.0),
    "disintegrant_starch": (3.0, 6.0),
    "disintegrant_other": (1.0, 2.0),
    "lubricant_stearate": (0.25, 0.5),
    "lubricant_other": (1.0, 2.0),
    "glidant": (1.0, 2.0),
    "film_coat": (1.0, 2.0),
    # Collapsed aliases retained for backward compatibility only
    "non_critical": (5.0, 10.0),  # filler-like
    "critical": (0.5, 1.0),  # maps to binder (tightest common functional band)
}

_LEVEL_TESTS: dict[SupacLevel, list[str]] = {
    1: [
        "Application/compendial release and identity testing",
        "Stability: one batch on long-term conditions (commitment)",
    ],
    2: [
        "Multi-point dissolution profile comparison (f2) vs approved product",
        "Stability: one batch, 3 months accelerated + long-term commitment",
    ],
    3: [
        "Multi-point dissolution profile comparison (f2) vs approved product",
        "In vivo bioequivalence study (when dissolution alone is insufficient)",
        "Stability: three batches, 3 months accelerated + long-term commitment",
    ],
}


@dataclass(frozen=True)
class SupacClassification:
    """SUPAC-IR style screening classification for a component change.

    Parameters
    ----------
    level : {1, 2, 3}
        Screened change level (1 = small, 2 = moderate, 3 = large).
    change_pct : float
        Absolute percent change supplied by the caller.
    component_category : str
        Excipient functional class used for threshold selection.
    rationale : str
        Human-readable explanation of the level assignment.
    recommended_tests : list[str]
        Screening-level recommended tests for the assigned level.
    """

    level: SupacLevel
    change_pct: float
    component_category: str
    rationale: str
    recommended_tests: list[str]


@dataclass(frozen=True)
class AlcoholDoseDumpingResult:
    """f2-based alcohol dose-dumping screening result.

    Parameters
    ----------
    control_label : str
        Label for the aqueous control medium.
    f2_by_ethanol_pct : dict[float, float]
        f2 of each ethanol medium vs the control profile, keyed by ethanol %.
    f2_threshold : float
        Similarity threshold applied (default 50).
    overall_pass : bool
        True if every ethanol medium has f2 >= f2_threshold.
    """

    control_label: str
    f2_by_ethanol_pct: dict[float, float]
    f2_threshold: float
    overall_pass: bool


def classify_supac_ir_level(
    change_pct: float,
    component_category: ComponentCategory | str,
) -> SupacClassification:
    """Classify a SUPAC-IR composition change level by excipient function.

    Screening only. Does not implement cumulative multi-component totals,
    site/scale/equipment changes, or biowaiver eligibility.

    Function-specific Level 1 / Level 2 ceilings (% of total formulation weight)
    ---------------------------------------------------------------------------
    filler                 : L1 <= 5%,   L2 <= 10%
    binder                 : L1 <= 0.5%, L2 <= 1%
    disintegrant_starch    : L1 <= 3%,   L2 <= 6%
    disintegrant_other     : L1 <= 1%,   L2 <= 2%
    lubricant_stearate     : L1 <= 0.25%, L2 <= 0.5%  (Ca/Mg stearate)
    lubricant_other        : L1 <= 1%,   L2 <= 2%
    glidant                : L1 <= 1%,   L2 <= 2%
    film_coat              : L1 <= 1%,   L2 <= 2%

    Deprecated aliases: ``non_critical`` (filler), ``critical`` (binder band).

    Parameters
    ----------
    change_pct : float
        Absolute magnitude of the component change as percent of total target
        dosage-form weight. Must be >= 0.
    component_category : str
        Excipient functional class (see table above).

    Returns
    -------
    SupacClassification
        Frozen result with level, rationale, and recommended tests.

    Raises
    ------
    ValueError
        If change_pct is negative or non-finite, or component_category is
        not a supported value.

    References
    ----------
    FDA Guidance for Industry: Immediate Release Solid Oral Dosage Forms:
    Scale-Up and Postapproval Changes (SUPAC-IR, 1995). CDER.
    """
    cat = str(component_category)
    if cat not in _THRESHOLDS:
        raise ValueError(
            f"component_category must be one of {sorted(_THRESHOLDS)!r} (got {cat!r})."
        )
    pct = float(change_pct)
    if pct != pct or pct == float("inf") or pct == float("-inf"):  # NaN/inf
        raise ValueError(f"change_pct must be finite (got {change_pct!r}).")
    if pct < 0.0:
        raise ValueError(f"change_pct must be >= 0 (got {pct}).")

    l1_max, l2_max = _THRESHOLDS[cat]
    if pct <= l1_max:
        level: SupacLevel = 1
        band = f"<= {l1_max:g}%"
    elif pct <= l2_max:
        level = 2
        band = f"{l1_max:g}% < change <= {l2_max:g}%"
    else:
        level = 3
        band = f"> {l2_max:g}%"

    alias_note = ""
    if cat in ("non_critical", "critical"):
        alias_note = (
            f" Note: {cat!r} is a deprecated collapsed alias; prefer an "
            "excipient-function class (filler, binder, disintegrant_*, "
            "lubricant_*, glidant, film_coat)."
        )

    rationale = (
        f"Screening Level {level} for component_category={cat!r} "
        f"with |change|={pct:g}% (band: {band}). "
        f"SUPAC-IR function table: L1 <= {l1_max:g}%, L2 <= {l2_max:g}%, else L3."
        f"{alias_note} "
        "Screening only; see FDA SUPAC-IR 1995 for full classification."
    )
    return SupacClassification(
        level=level,
        change_pct=pct,
        component_category=cat,
        rationale=rationale,
        recommended_tests=list(_LEVEL_TESTS[level]),
    )


def alcohol_dose_dumping_assessment(
    control_means: Sequence[float],
    eth_means_by_pct: Mapping[float, Sequence[float]],
    time_points: Sequence[float] | None = None,
    f2_threshold: float = 50.0,
    *,
    control_label: str = "control",
) -> AlcoholDoseDumpingResult:
    """Screen alcohol dose-dumping risk via f2 vs aqueous control.

    For each ethanol medium (keyed by ethanol percent), computes the f2
    similarity factor against the control medium mean profile. Profiles that
    remain similar (f2 >= threshold) are less consistent with alcohol-driven
    dose dumping; failure indicates a need for further evaluation.

    Parameters
    ----------
    control_means : Sequence[float]
        Mean percent dissolved in the aqueous control medium at each time
        point (aligned arrays).
    eth_means_by_pct : Mapping[float, Sequence[float]]
        Map of ethanol percent (e.g. 5, 20, 40) to mean percent-dissolved
        profiles aligned to the same time points as ``control_means``.
    time_points : Sequence[float] or None, optional
        Optional time grid (minutes). Not used in the f2 calculation but
        accepted for API completeness / caller documentation. Must match
        profile length if provided.
    f2_threshold : float, optional
        Similarity threshold, by default 50.0 (FDA 1997 f2 criterion).
    control_label : str, optional
        Label for the control medium, by default ``"control"``.

    Returns
    -------
    AlcoholDoseDumpingResult
        Per-ethanol f2 values and overall pass/fail.

    Raises
    ------
    ValueError
        If eth_means_by_pct is empty, f2_threshold is not positive, time
        points length mismatches, or f2 validation fails for any profile.

    Notes
    -----
    This is a dissolution-similarity screen, not a full dose-dumping clinical
    assessment. Regulatory context for alcohol media is typically modified-
    release products; applying the same f2 screen to IR data is a transparent
    descriptive comparison only.

    References
    ----------
    FDA Guidance for Industry: Dissolution Testing of Immediate Release
    Solid Oral Dosage Forms (1997). CDER. (f2 criterion)

    FDA Guidance for Industry: Immediate Release Solid Oral Dosage Forms:
    Scale-Up and Postapproval Changes (SUPAC-IR, 1995). CDER.
    """
    if not eth_means_by_pct:
        raise ValueError("eth_means_by_pct must contain at least one ethanol medium.")
    thr = float(f2_threshold)
    if thr <= 0.0:
        raise ValueError(f"f2_threshold must be > 0 (got {thr}).")

    n = len(control_means)
    if time_points is not None and len(time_points) != n:
        raise ValueError(
            f"time_points length ({len(time_points)}) must match control_means length ({n})."
        )

    f2_by: dict[float, float] = {}
    for eth_pct, means in eth_means_by_pct.items():
        key = float(eth_pct)
        if len(means) != n:
            raise ValueError(
                f"Ethanol {key:g}% profile length ({len(means)}) must match "
                f"control_means length ({n})."
            )
        f2_by[key] = f2(control_means, means)

    overall = all(v >= thr for v in f2_by.values())
    return AlcoholDoseDumpingResult(
        control_label=control_label,
        f2_by_ethanol_pct=f2_by,
        f2_threshold=thr,
        overall_pass=overall,
    )
