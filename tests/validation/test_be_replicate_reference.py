"""Replicate BE validation against external R/SAS-compatible scalar fixtures.

Scope
-----
These fixtures validate OpenPKFlow's transparent scalar screening summaries:
GMR, conventional subject-difference CI, CVwR, EMA-style scaled limits, and the
FDA-style RSABE point criterion. They do not claim full FDA RSABE 95% upper-bound
or SAS PROC MIXED parity.
"""

from __future__ import annotations

import math

import pandas as pd
import pytest

from openpkflow.be import cv_to_s_within, replicate_be

_REPLICATE_REFERENCE: dict[str, dict[str, float | int | bool]] = {
    "partial_highvar": {
        "n": 12,
        "ratio": 1.05,
        "cv_wr": 0.40,
        "gmr": 1.050000000000,
        "gmr_lower_90ci": 1.050000000000,
        "gmr_upper_90ci": 1.050000000000,
        "cv_wr_pct": 40.000000000000,
        "swr": 0.385253170160,
        "scaled_lower": 0.746177024015,
        "scaled_upper": 1.340164555884,
        "rsabe_point_criterion": -0.115864062577,
    },
    "partial_lowvar": {
        "n": 12,
        "ratio": 1.00,
        "cv_wr": 0.10,
        "gmr": 1.000000000000,
        "gmr_lower_90ci": 1.000000000000,
        "gmr_upper_90ci": 1.000000000000,
        "cv_wr_pct": 10.000000000000,
        "swr": 0.099751345120,
        "scaled_lower": 0.800000000000,
        "scaled_upper": 1.250000000000,
        "rsabe_point_criterion": -0.007927316270,
    },
    "partial_cap": {
        "n": 24,
        "ratio": 1.20,
        "cv_wr": 0.50,
        "gmr": 1.200000000000,
        "scaled_lower": 0.698367819781,
        "scaled_upper": 1.431910193562,
        "rsabe_point_criterion": -0.144534798391,
    },
    "partial_fail_point": {
        "n": 24,
        "ratio": 1.30,
        "cv_wr": 0.40,
        "gmr": 1.300000000000,
        "scaled_lower": 0.746177024015,
        "scaled_upper": 1.340164555884,
        "abe_pass": False,
        "scaled_abe_pass": False,
        "rsabe_point_pass": False,
    },
}


def _partial_replicate_df(n: int, ratio: float, cv_wr: float) -> pd.DataFrame:
    swr = cv_to_s_within(cv_wr)
    sequences = ["TRR", "RTR", "RRT"]
    rows: list[dict[str, object]] = []
    for i in range(n):
        subject = f"S{i + 1:02d}"
        sequence = sequences[i % len(sequences)]
        base = 100.0 + i
        ref_logs = [
            math.log(base) - swr / math.sqrt(2.0),
            math.log(base) + swr / math.sqrt(2.0),
        ]
        test_log = math.log(base * ratio)
        r_index = 0
        for period, treatment in enumerate(sequence, start=1):
            if treatment == "R":
                value = math.exp(ref_logs[r_index])
                r_index += 1
            else:
                value = math.exp(test_log)
            rows.append(
                {
                    "subject": subject,
                    "sequence": sequence,
                    "period": period,
                    "treatment": treatment,
                    "AUCinf": value,
                }
            )
    return pd.DataFrame(rows)


class TestReplicateBEReference:
    @pytest.mark.parametrize("name", sorted(_REPLICATE_REFERENCE))
    def test_partial_replicate_scalar_reference(self, name: str) -> None:
        s = _REPLICATE_REFERENCE[name]
        result = replicate_be(
            _partial_replicate_df(int(s["n"]), float(s["ratio"]), float(s["cv_wr"])),
            value_col="AUCinf",
        )
        assert result.gmr == pytest.approx(float(s["gmr"]), abs=1e-12)
        if "gmr_lower_90ci" in s:
            assert result.gmr_lower_90ci == pytest.approx(float(s["gmr_lower_90ci"]), abs=1e-12)
        if "gmr_upper_90ci" in s:
            assert result.gmr_upper_90ci == pytest.approx(float(s["gmr_upper_90ci"]), abs=1e-12)
        if "cv_wr_pct" in s:
            assert result.cv_wr_pct == pytest.approx(float(s["cv_wr_pct"]), abs=1e-10)
        if "swr" in s:
            assert result.swr == pytest.approx(float(s["swr"]), abs=1e-12)
        assert result.scaled_lower == pytest.approx(float(s["scaled_lower"]), abs=1e-12)
        assert result.scaled_upper == pytest.approx(float(s["scaled_upper"]), abs=1e-12)
        if "rsabe_point_criterion" in s:
            assert result.rsabe_point_criterion == pytest.approx(
                float(s["rsabe_point_criterion"]), abs=1e-12
            )
        if "abe_pass" in s:
            assert result.abe_pass is s["abe_pass"]
        if "scaled_abe_pass" in s:
            assert result.scaled_abe_pass is s["scaled_abe_pass"]
        if "rsabe_point_pass" in s:
            assert result.rsabe_point_pass is s["rsabe_point_pass"]
