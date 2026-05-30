"""Tests for replicate-design BE screening utilities."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from openpkflow.be import (
    cv_to_s_within,
    ema_scaled_limits,
    replicate_be,
    s_within_to_cv_pct,
)


def _partial_replicate_df(n: int = 12, ratio: float = 1.05, cv_wr: float = 0.40) -> pd.DataFrame:
    """Build a deterministic TRR/RTR/RRT-style dataset."""
    swr = cv_to_s_within(cv_wr)
    sequences = ["TRR", "RTR", "RRT"]
    rows: list[dict[str, object]] = []
    for i in range(n):
        subject = f"S{i + 1:02d}"
        sequence = sequences[i % len(sequences)]
        base = 100.0 + i
        # Symmetric reference replicate offsets make each subject's reference
        # mean equal to base on the log scale and estimate CVwR exactly.
        ref_logs = [math.log(base) - swr / math.sqrt(2.0), math.log(base) + swr / math.sqrt(2.0)]
        test_logs = [math.log(base * ratio)]
        r_index = 0
        t_index = 0
        for period, treatment in enumerate(sequence, start=1):
            if treatment == "R":
                value = math.exp(ref_logs[r_index])
                r_index += 1
            else:
                value = math.exp(test_logs[t_index])
                t_index += 1
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


class TestReplicateBEConversions:
    def test_cv_round_trip(self) -> None:
        swr = cv_to_s_within(0.40)
        assert s_within_to_cv_pct(swr) == pytest.approx(40.0, abs=1e-10)

    def test_ema_scaled_limits_standard_below_30pct(self) -> None:
        swr = cv_to_s_within(0.20)
        assert ema_scaled_limits(swr) == pytest.approx((0.80, 1.25), abs=1e-12)

    def test_ema_scaled_limits_scale_above_30pct(self) -> None:
        swr = cv_to_s_within(0.40)
        lower, upper = ema_scaled_limits(swr)
        assert lower < 0.80
        assert upper > 1.25
        assert lower == pytest.approx(1.0 / upper)

    def test_ema_scaled_limits_cap_at_50pct_cvwr(self) -> None:
        lower_50, upper_50 = ema_scaled_limits(cv_to_s_within(0.50))
        lower_80, upper_80 = ema_scaled_limits(cv_to_s_within(0.80))
        assert lower_80 == pytest.approx(lower_50)
        assert upper_80 == pytest.approx(upper_50)


class TestReplicateBE:
    def test_partial_replicate_estimates_gmr_and_cvwr(self) -> None:
        df = _partial_replicate_df(n=12, ratio=1.05, cv_wr=0.40)
        result = replicate_be(df, value_col="AUCinf")
        assert result.n_subjects == 12
        assert result.design == "RRT/RTR/TRR"
        assert result.gmr == pytest.approx(1.05, rel=1e-12)
        assert result.cv_wr_pct == pytest.approx(40.0, abs=1e-10)
        assert result.scaled_lower < 0.80
        assert result.scaled_upper > 1.25
        assert result.rsabe_point_pass is True
        assert "Research-grade" in result.analysis_note

    def test_conventional_abe_can_pass_for_low_variability(self) -> None:
        df = _partial_replicate_df(n=12, ratio=1.00, cv_wr=0.10)
        result = replicate_be(df, value_col="AUCinf")
        assert result.abe_pass is True
        assert result.scaled_abe_pass is True
        assert result.scaled_lower == pytest.approx(0.80)
        assert result.scaled_upper == pytest.approx(1.25)

    def test_rejects_nonpositive_values(self) -> None:
        df = _partial_replicate_df()
        df.loc[0, "AUCinf"] = 0.0
        with pytest.raises(ValueError, match="positive"):
            replicate_be(df, value_col="AUCinf")

    def test_rejects_unknown_treatment_label(self) -> None:
        df = _partial_replicate_df()
        df.loc[0, "treatment"] = "P"
        with pytest.raises(ValueError, match="Unknown treatment"):
            replicate_be(df, value_col="AUCinf")

    def test_requires_repeated_reference_observations(self) -> None:
        df = pd.DataFrame(
            {
                "subject": ["S1", "S1", "S2", "S2"],
                "sequence": ["TR", "TR", "RT", "RT"],
                "period": [1, 2, 1, 2],
                "treatment": ["T", "R", "R", "T"],
                "AUCinf": [105.0, 100.0, 100.0, 105.0],
            }
        )
        with pytest.raises(ValueError, match="repeated reference"):
            replicate_be(df, value_col="AUCinf")
