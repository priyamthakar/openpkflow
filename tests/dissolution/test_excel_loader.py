"""Tests for DissolutionStudy.from_excel() and load_dissolution_excel().

Reference: mirrors test coverage of load_dissolution_csv() in test_study.py.
"""

from __future__ import annotations

import pytest

pytest.importorskip("openpyxl", reason="openpyxl required for Excel tests")

import pandas as pd  # noqa: E402

from openpkflow.dissolution import (  # noqa: E402
    DissolutionCSVConfig,
    DissolutionStudy,
    load_dissolution_excel,
)


def _make_excel(tmp_path, data: dict, sheet_name: str = "Sheet1") -> str:
    """Write a minimal dissolution DataFrame to an Excel file and return the path."""
    df = pd.DataFrame(data)
    path = tmp_path / "dissolution.xlsx"
    df.to_excel(path, index=False, sheet_name=sheet_name)
    return str(path)


_VALID_DATA = {
    "formulation": ["ref", "ref", "ref", "test", "test", "test"],
    "batch": ["B1", "B1", "B1", "B2", "B2", "B2"],
    "time": [15, 30, 45, 15, 30, 45],
    "percent_released": [40.0, 65.0, 85.0, 42.0, 63.0, 83.0],
}


class TestLoadDissolutionExcel:
    def test_happy_path(self, tmp_path):
        """Round-trip: write Excel, load, check dtypes and row count."""
        path = _make_excel(tmp_path, _VALID_DATA)
        df = load_dissolution_excel(path)
        assert list(df.columns) == ["formulation", "batch", "time", "percent_released"]
        assert len(df) == 6
        assert df["time"].dtype == float
        assert df["percent_released"].dtype == float

    def test_sheet_name_by_string(self, tmp_path):
        """Loads correctly when sheet_name is passed as a string."""
        path = _make_excel(tmp_path, _VALID_DATA, sheet_name="Data")
        df = load_dissolution_excel(path, sheet_name="Data")
        assert len(df) == 6

    def test_sheet_name_by_index(self, tmp_path):
        """Loads correctly when sheet_name is passed as int index 0."""
        path = _make_excel(tmp_path, _VALID_DATA)
        df = load_dissolution_excel(path, sheet_name=0)
        assert len(df) == 6

    def test_custom_config(self, tmp_path):
        """Custom column names are respected."""
        data = {
            "form": ["ref", "ref", "test", "test"],
            "lot": ["L1", "L1", "L2", "L2"],
            "t": [15, 30, 15, 30],
            "pct": [40.0, 65.0, 42.0, 63.0],
        }
        df_src = pd.DataFrame(data)
        path = tmp_path / "custom.xlsx"
        df_src.to_excel(path, index=False)
        cfg = DissolutionCSVConfig(
            formulation_col="form",
            batch_col="lot",
            time_col="t",
            percent_released_col="pct",
        )
        df = load_dissolution_excel(str(path), config=cfg)
        assert set(df.columns) == {"formulation", "batch", "time", "percent_released"}
        assert len(df) == 4

    def test_file_not_found(self):
        """FileNotFoundError is raised for a non-existent path."""
        with pytest.raises(FileNotFoundError, match="not found"):
            load_dissolution_excel("/nonexistent/path/file.xlsx")

    def test_missing_column(self, tmp_path):
        """ValueError is raised when a required column is absent."""
        data = {k: v for k, v in _VALID_DATA.items() if k != "batch"}
        path = _make_excel(tmp_path, data)
        with pytest.raises(ValueError, match="batch"):
            load_dissolution_excel(path)

    def test_negative_time_rejected(self, tmp_path):
        """ValueError is raised for negative time values."""
        data = {**_VALID_DATA, "time": [-5, 30, 45, 15, 30, 45]}
        path = _make_excel(tmp_path, data)
        with pytest.raises(ValueError, match="negative"):
            load_dissolution_excel(path)

    def test_out_of_range_pct_rejected(self, tmp_path):
        """ValueError is raised when percent_released is outside [0, 100]."""
        data = {**_VALID_DATA, "percent_released": [40.0, 65.0, 110.0, 42.0, 63.0, 83.0]}
        path = _make_excel(tmp_path, data)
        with pytest.raises(ValueError, match="outside \\[0, 100\\]"):
            load_dissolution_excel(path)


class TestDissolutionStudyFromExcel:
    def test_from_excel_returns_study(self, tmp_path):
        """DissolutionStudy.from_excel() returns a usable DissolutionStudy."""
        path = _make_excel(tmp_path, _VALID_DATA)
        study = DissolutionStudy.from_excel(path)
        assert "ref" in study.formulations()
        assert "test" in study.formulations()

    def test_from_excel_compare(self, tmp_path):
        """from_excel() produces a study that can run compare()."""
        path = _make_excel(tmp_path, _VALID_DATA)
        study = DissolutionStudy.from_excel(path)
        result = study.compare("ref", "test")
        assert 0.0 <= result.f2_value <= 100.0

    def test_from_excel_sheet_name(self, tmp_path):
        """sheet_name parameter is forwarded correctly."""
        path = _make_excel(tmp_path, _VALID_DATA, sheet_name="Results")
        study = DissolutionStudy.from_excel(path, sheet_name="Results")
        assert len(study.formulations()) == 2

    def test_from_excel_file_not_found(self):
        """FileNotFoundError is raised for a non-existent file."""
        with pytest.raises(FileNotFoundError):
            DissolutionStudy.from_excel("/nonexistent/file.xlsx")

    def test_from_excel_vs_from_csv_same_result(self, tmp_path):
        """from_excel() and from_csv() on equivalent data produce identical f2."""
        import csv

        csv_path = tmp_path / "dissolution.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(_VALID_DATA.keys()))
            writer.writeheader()
            rows = [
                {k: _VALID_DATA[k][i] for k in _VALID_DATA}
                for i in range(len(_VALID_DATA["formulation"]))
            ]
            writer.writerows(rows)

        xlsx_path = _make_excel(tmp_path, _VALID_DATA)

        result_csv = DissolutionStudy.from_csv(csv_path).compare("ref", "test")
        result_xlsx = DissolutionStudy.from_excel(xlsx_path).compare("ref", "test")

        assert abs(result_csv.f2_value - result_xlsx.f2_value) < 1e-9
