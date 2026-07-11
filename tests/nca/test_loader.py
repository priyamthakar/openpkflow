"""Unit tests for openpkflow.nca.loader.load_nca_csv."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pandas as pd
import pytest

from openpkflow.nca.loader import load_nca_csv


def _write_csv(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "test.csv"
    p.write_text(textwrap.dedent(content).strip(), encoding="utf-8")
    return p


_BASIC_CSV = """\
    subject,time,conc,dose,route
    1,0.0,0.0,320.0,oral
    1,1.0,5.0,320.0,oral
    1,2.0,3.0,320.0,oral
    2,0.0,0.0,300.0,oral
    2,1.0,4.0,300.0,oral
    2,2.0,2.0,300.0,oral
"""


class TestLoadNcaCsvHappyPath:
    def test_basic_load(self, tmp_path: Path) -> None:
        p = _write_csv(tmp_path, _BASIC_CSV)
        df = load_nca_csv(p)
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns[:5]) == ["subject", "time", "conc", "dose", "route"]

    def test_row_count(self, tmp_path: Path) -> None:
        p = _write_csv(tmp_path, _BASIC_CSV)
        df = load_nca_csv(p)
        assert len(df) == 6

    def test_sorted_by_subject_then_time(self, tmp_path: Path) -> None:
        csv = """\
            subject,time,conc,dose,route
            2,2.0,2.0,300.0,oral
            2,0.0,0.0,300.0,oral
            1,2.0,3.0,320.0,oral
            1,0.0,0.0,320.0,oral
        """
        p = _write_csv(tmp_path, csv)
        df = load_nca_csv(p)
        subjects = df["subject"].tolist()
        assert subjects == ["1", "1", "2", "2"]
        times_s1 = df.loc[df["subject"] == "1", "time"].tolist()
        assert times_s1 == [0.0, 2.0]

    def test_conc_is_float(self, tmp_path: Path) -> None:
        p = _write_csv(tmp_path, _BASIC_CSV)
        df = load_nca_csv(p)
        assert df["conc"].dtype == float

    def test_dose_is_float(self, tmp_path: Path) -> None:
        p = _write_csv(tmp_path, _BASIC_CSV)
        df = load_nca_csv(p)
        assert df["dose"].dtype == float


class TestLoadNcaCsvBLQHandling:
    def _blq_csv(self, tmp_path: Path) -> Path:
        csv = """\
            subject,time,conc,dose,route,blq
            1,0.0,0.0,320.0,oral,0
            1,1.0,5.0,320.0,oral,0
            1,2.0,3.0,320.0,oral,0
            1,4.0,0.2,320.0,oral,1
            1,8.0,0.1,320.0,oral,1
        """
        return _write_csv(tmp_path, csv)

    def test_blq_method_none_without_blq_flags_keeps_all_rows(self, tmp_path: Path) -> None:
        """blq_method='none' is allowed only when no BLQ flags/markers are present."""
        p = _write_csv(tmp_path, _BASIC_CSV)
        df = load_nca_csv(p, blq_method="none")
        assert len(df) == 6

    def test_blq_method_none_with_flags_raises(self, tmp_path: Path) -> None:
        """Fail closed: BLQ flags with method 'none' must not pass through as observed.

        Reference: pharmacometric correctness rule 4 (explicit BLQ handling).
        """
        p = self._blq_csv(tmp_path)
        with pytest.raises(ValueError, match="BLQ observation"):
            load_nca_csv(p, blq_col="blq", blq_method="none")

    def test_string_blq_with_none_raises(self, tmp_path: Path) -> None:
        """Strings like '<0.5' must not silently become observed 0.5 under method none."""
        csv = """\
            subject,time,conc,dose,route
            1,0.0,0.0,320.0,oral
            1,1.0,5.0,320.0,oral
            1,2.0,<0.5,320.0,oral
        """
        p = _write_csv(tmp_path, csv)
        with pytest.raises(ValueError, match="BLQ observation"):
            load_nca_csv(p, blq_method="none")

    def test_blq_method_drop(self, tmp_path: Path) -> None:
        p = self._blq_csv(tmp_path)
        df = load_nca_csv(p, blq_col="blq", blq_method="drop")
        # 5 rows - 2 BLQ rows = 3 rows; first row has conc=0 but blq=0 so stays
        assert len(df) == 3
        assert df["time"].tolist() == pytest.approx([0.0, 1.0, 2.0])

    def test_blq_method_zero(self, tmp_path: Path) -> None:
        p = self._blq_csv(tmp_path)
        df = load_nca_csv(p, blq_col="blq", blq_method="zero")
        assert len(df) == 5
        blq_concs = df.loc[df.index[-2:], "conc"].tolist()
        assert all(v == 0.0 for v in blq_concs)

    def test_blq_method_half_lloq(self, tmp_path: Path) -> None:
        p = self._blq_csv(tmp_path)
        df = load_nca_csv(p, blq_col="blq", blq_method="half_lloq", lloq=1.0)
        blq_rows = df.iloc[-2:]
        assert all(v == pytest.approx(0.5) for v in blq_rows["conc"].tolist())

    def test_blq_method_lloq(self, tmp_path: Path) -> None:
        p = self._blq_csv(tmp_path)
        df = load_nca_csv(p, blq_col="blq", blq_method="lloq", lloq=0.5)
        blq_rows = df.iloc[-2:]
        assert all(v == pytest.approx(0.5) for v in blq_rows["conc"].tolist())

    def test_alias_m1_equals_drop(self, tmp_path: Path) -> None:
        p = self._blq_csv(tmp_path)
        df = load_nca_csv(p, blq_col="blq", blq_method="m1")
        assert len(df) == 3

    def test_alias_m2_equals_zero(self, tmp_path: Path) -> None:
        p = self._blq_csv(tmp_path)
        df = load_nca_csv(p, blq_col="blq", blq_method="m2")
        assert len(df) == 5

    def test_string_blq_parsed(self, tmp_path: Path) -> None:
        csv = """\
            subject,time,conc,dose,route
            1,0.0,0.0,320.0,oral
            1,1.0,5.0,320.0,oral
            1,2.0,<0.5,320.0,oral
        """
        p = _write_csv(tmp_path, csv)
        df = load_nca_csv(p, blq_method="zero")
        assert df.loc[df["time"] == 2.0, "conc"].iloc[0] == pytest.approx(0.0)

    def test_string_blq_drop(self, tmp_path: Path) -> None:
        csv = """\
            subject,time,conc,dose,route
            1,0.0,0.0,320.0,oral
            1,1.0,5.0,320.0,oral
            1,2.0,< 2.0,320.0,oral
        """
        p = _write_csv(tmp_path, csv)
        df = load_nca_csv(p, blq_method="drop")
        assert len(df) == 2


class TestLoadNcaCsvErrors:
    def test_missing_required_column(self, tmp_path: Path) -> None:
        csv = """\
            subject,time,conc,dose
            1,0.0,1.0,320.0
        """
        p = _write_csv(tmp_path, csv)
        with pytest.raises(ValueError, match="route"):
            load_nca_csv(p)

    def test_unknown_blq_method_raises(self, tmp_path: Path) -> None:
        p = _write_csv(tmp_path, _BASIC_CSV)
        with pytest.raises(ValueError, match="Unknown blq_method"):
            load_nca_csv(p, blq_method="mean_impute")

    def test_half_lloq_without_lloq_raises(self, tmp_path: Path) -> None:
        p = _write_csv(tmp_path, _BASIC_CSV)
        with pytest.raises(ValueError, match="lloq"):
            load_nca_csv(p, blq_method="half_lloq")

    def test_lloq_without_lloq_value_raises(self, tmp_path: Path) -> None:
        p = _write_csv(tmp_path, _BASIC_CSV)
        with pytest.raises(ValueError, match="lloq"):
            load_nca_csv(p, blq_method="lloq")

    def test_missing_blq_col_raises(self, tmp_path: Path) -> None:
        p = _write_csv(tmp_path, _BASIC_CSV)
        with pytest.raises(ValueError, match="blq_col"):
            load_nca_csv(p, blq_col="nonexistent_col")
