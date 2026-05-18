"""Tests for pop.dataset module."""

import pytest

from openpkflow.pop.dataset import PopCSVConfig, create_nonmem_dataset, load_pop_csv


class TestCreateNonmemDataset:
    def test_basic_structure(self):
        df = create_nonmem_dataset(
            subject_id="S1",
            dose_times=[0.0, 24.0],
            dose_amounts=[100.0, 100.0],
            obs_times=[1.0, 4.0, 8.0, 12.0],
            obs_dv=[5.2, 8.1, 6.4, 3.2],
        )
        assert "ID" in df.columns
        assert "TIME" in df.columns
        assert "DV" in df.columns
        assert "AMT" in df.columns
        assert "EVID" in df.columns
        assert "MDV" in df.columns

    def test_evid_values(self):
        df = create_nonmem_dataset(
            subject_id=1,
            dose_times=[0.0],
            dose_amounts=[100.0],
            obs_times=[1.0, 4.0],
            obs_dv=[5.0, 3.0],
        )
        dose_rows = df[df["EVID"] == 1]
        obs_rows = df[df["EVID"] == 0]
        assert len(dose_rows) == 1
        assert len(obs_rows) == 2

    def test_sorted_by_time(self):
        df = create_nonmem_dataset(
            subject_id="S1",
            dose_times=[0.0, 24.0],
            dose_amounts=[100.0, 100.0],
            obs_times=[2.0, 26.0],
            obs_dv=[4.0, 3.0],
        )
        times = df["TIME"].values
        assert all(times[i] <= times[i + 1] for i in range(len(times) - 1))

    def test_mdv_for_dose_records(self):
        df = create_nonmem_dataset(
            subject_id="S1",
            dose_times=[0.0],
            dose_amounts=[100.0],
            obs_times=[2.0],
            obs_dv=[5.0],
        )
        assert int(df[df["EVID"] == 1]["MDV"].values[0]) == 1
        assert int(df[df["EVID"] == 0]["MDV"].values[0]) == 0

    def test_mismatched_dose_lengths_raises(self):
        with pytest.raises(ValueError, match="dose_times length"):
            create_nonmem_dataset(
                subject_id=1,
                dose_times=[0.0, 24.0],
                dose_amounts=[100.0],
                obs_times=[1.0],
                obs_dv=[5.0],
            )

    def test_mismatched_obs_lengths_raises(self):
        with pytest.raises(ValueError, match="obs_times length"):
            create_nonmem_dataset(
                subject_id=1,
                dose_times=[0.0],
                dose_amounts=[100.0],
                obs_times=[1.0, 2.0],
                obs_dv=[5.0],
            )


class TestLoadPopCSV:
    def test_load_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_pop_csv(tmp_path / "nonexistent.csv")

    def test_load_missing_column_raises(self, tmp_path):
        csv = tmp_path / "bad.csv"
        csv.write_text("ID,TIME\n1,0\n")
        with pytest.raises(ValueError, match="Required columns missing"):
            load_pop_csv(csv)

    def test_load_filters_evid(self, tmp_path):
        csv = tmp_path / "pop.csv"
        csv.write_text("ID,TIME,DV,EVID,MDV\n1,0,0,1,1\n1,1,5.2,0,0\n1,2,3.1,0,0\n")
        df = load_pop_csv(csv, obs_only=True)
        assert len(df) == 2
        assert (df["EVID"] == 0).all()

    def test_load_no_filter(self, tmp_path):
        csv = tmp_path / "pop.csv"
        csv.write_text("ID,TIME,DV,EVID,MDV\n1,0,0,1,1\n1,1,5.2,0,0\n")
        df = load_pop_csv(csv, obs_only=False)
        assert len(df) == 2

    def test_custom_config(self, tmp_path):
        csv = tmp_path / "pop.csv"
        csv.write_text("SUBJ,NOM_TIME,CONC\n1,0,5.2\n1,2,3.1\n")
        cfg = PopCSVConfig(id_col="SUBJ", time_col="NOM_TIME", dv_col="CONC")
        df = load_pop_csv(csv, cfg)
        assert "SUBJ" in df.columns
        assert len(df) == 2
