"""Tests for result export methods and lazy subpackage access."""

from __future__ import annotations

import dataclasses
import importlib
import inspect
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from openpkflow._export import dataclass_to_dict, to_builtin
from openpkflow.be import BEStudy, be_tost, fda_partial_replicate_rsabe, formal_be_anova
from openpkflow.datasets import example_theoph_path
from openpkflow.dissolution import (
    ComparisonResult,
    alcohol_dose_dumping_assessment,
    bootstrap_f2,
    fit_dissolution_models,
    model_dependent_comparison,
    msd,
    msd_vessels,
)
from openpkflow.dissolution.multi_media import MultiMediaResult
from openpkflow.ivivc import level_c_correlation
from openpkflow.nca import AUCResult, NCAStudy, lambda_z
from openpkflow.pop import GOFResult, simulate_vpc
from openpkflow.sim.dosing import DoseRegimen
from openpkflow.sim.models import OneCompartmentModel

DATA = Path(__file__).parent / "validation" / "data"
SUBPACKAGES = ["dissolution", "nca", "be", "ivivc", "sim", "bayes", "pop", "pipeline"]
TIMES = [10.0, 20.0, 30.0, 45.0, 60.0]
REF = [22.0, 41.0, 58.0, 76.0, 88.0]
TEST = [20.0, 39.0, 57.0, 74.0, 86.0]


def _public_result_classes() -> list[type]:
    classes = []
    for name in SUBPACKAGES:
        module = importlib.import_module(f"openpkflow.{name}")
        for attr in getattr(module, "__all__", dir(module)):
            obj = getattr(module, attr, None)
            if inspect.isclass(obj) and attr.endswith(("Result", "Results")):
                classes.append(obj)
    return classes


@pytest.mark.parametrize("cls", _public_result_classes(), ids=lambda c: c.__name__)
def test_every_public_result_class_has_to_dict(cls: type) -> None:
    """Every exported result class offers to_dict()."""
    assert callable(getattr(cls, "to_dict", None))


def _vessels(means: list[float], seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return np.asarray(means) + rng.normal(0.0, 1.5, size=(12, len(means)))


@pytest.fixture(scope="module")
def results() -> dict[str, object]:
    """Real result objects built through the public API."""
    ref_v = _vessels(REF, 1)
    test_v = _vessels(TEST, 2)
    vpc_model = OneCompartmentModel(route="oral", CL_F=5.0, Vz_F=50.0, ka=1.2)
    vpc_regimen = DoseRegimen.from_repeated(amount=100.0, route="oral", tau=24.0, n_doses=1)
    observed = pd.DataFrame({"TIME": [1, 2, 4, 8, 12], "DV": [1.5, 1.6, 1.3, 0.8, 0.5]})
    comparison = ComparisonResult(
        reference_label="reference",
        test_label="test",
        f1_value=2.0,
        f2_value=85.0,
        n_timepoints=len(TIMES),
        reference_mean=REF,
        test_mean=TEST,
        time_points=TIMES,
    )
    be_df = pd.DataFrame(
        {
            "subject": ["S01", "S02", "S03", "S04", "S05", "S06"],
            "sequence": ["RT", "RT", "RT", "TR", "TR", "TR"],
            "reference": [100.2, 98.7, 105.1, 97.3, 102.8, 99.5],
            "test": [95.1, 94.0, 99.8, 92.9, 97.4, 94.8],
        }
    )
    return {
        "msd": msd(REF, TEST),
        "msd_vessels": msd_vessels(ref_v, test_v),
        "bootstrap_f2": bootstrap_f2(ref_v, test_v, n_replicates=200, seed=1),
        "model_comparison": model_dependent_comparison(TIMES, REF, TIMES, TEST, "weibull"),
        "fit": fit_dissolution_models(TIMES, REF, "reference"),
        "alcohol": alcohol_dose_dumping_assessment(REF, {20.0: TEST, 40.0: REF}),
        "comparison": comparison,
        "multi_media": MultiMediaResult(
            reference_label="reference",
            test_label="test",
            media_names=["pH 1.2", "pH 6.8"],
            per_media_results={"pH 1.2": comparison, "pH 6.8": comparison},
        ),
        "auc": AUCResult(value=12.5, warnings=[]),
        "lambda_z": lambda_z([1.0, 2.0, 4.0, 8.0, 12.0, 24.0], [9.0, 8.0, 6.2, 3.9, 2.4, 0.6]),
        "nca_summary": NCAStudy.from_csv(
            str(example_theoph_path()), auc_method="linear_up_log_down", blq_method="none"
        ).analyze(),
        "be": BEStudy(be_df, parameter="AUCinf").analyze(),
        "be_tost": be_tost(be_df["reference"].tolist(), be_df["test"].tolist()),
        "formal_be": formal_be_anova(
            pd.read_csv(DATA / "be_anova_balanced_2x2.csv"), parameter="AUCinf"
        ),
        "rsabe": fda_partial_replicate_rsabe(
            pd.read_csv(DATA / "be_rsabe_partial_replicate_patterson2012.csv"),
            parameter="AUC",
            value_col="AUC",
        ),
        "level_c": level_c_correlation([20.0, 30.0, 45.0], [110.0, 95.0, 80.0]),
        "gof": GOFResult(
            dv=[5.2, 8.1, 6.4, 3.2],
            pred=[4.9, 7.8, 6.0, 3.0],
            ipred=[5.1, 8.0, 6.3, 3.1],
            time=[1.0, 2.0, 4.0, 8.0],
            id=["S1", "S1", "S1", "S1"],
            sigma=0.15,
        ),
        "vpc": simulate_vpc(vpc_model, vpc_regimen, observed, n_replicates=50, seed=1, n_bins=4),
    }


@pytest.mark.parametrize(
    "key",
    [
        "msd",
        "msd_vessels",
        "bootstrap_f2",
        "model_comparison",
        "alcohol",
        "auc",
        "lambda_z",
        "nca_summary",
        "be",
        "be_tost",
        "formal_be",
        "rsabe",
        "level_c",
        "gof",
        "vpc",
    ],
)
def test_to_dict_is_json_serializable(results: dict[str, object], key: str) -> None:
    """New to_dict() methods return only built-in types that json can encode."""
    data = results[key].to_dict()  # type: ignore[attr-defined]
    assert isinstance(data, dict)
    assert json.loads(json.dumps(data)) is not None


def test_dataclass_to_dict_keeps_every_public_field(results: dict[str, object]) -> None:
    """Field-based to_dict() covers every dataclass field of the result."""
    rsabe = results["rsabe"]
    data = rsabe.to_dict()  # type: ignore[attr-defined]
    assert set(data) == {f.name for f in dataclasses.fields(rsabe)}  # type: ignore[arg-type]
    assert data["decision"] == rsabe.decision  # type: ignore[attr-defined]
    assert data["gmr"] == rsabe.gmr  # type: ignore[attr-defined]


def test_be_result_to_dict_includes_subject_rows(results: dict[str, object]) -> None:
    """BEResult.to_dict() converts the per-subject DataFrame to a list of rows."""
    data = results["be"].to_dict()  # type: ignore[attr-defined]
    assert len(data["subjects_df"]) == 6
    assert isinstance(data["subjects_df"][0], dict)


def test_nca_summary_to_dict_matches_dataframe(results: dict[str, object]) -> None:
    """NCASummaryResults.to_dict() lists one entry per subject, as to_dataframe() does."""
    summary = results["nca_summary"]
    data = summary.to_dict()  # type: ignore[attr-defined]
    assert data["auc_method"] == "linear_up_log_down"
    assert len(data["results"]) == len(summary.to_dataframe())  # type: ignore[attr-defined]


def test_comparison_to_dataframe(results: dict[str, object]) -> None:
    """ComparisonResult.to_dataframe() has one row per time point."""
    df = results["comparison"].to_dataframe()  # type: ignore[attr-defined]
    assert list(df.columns) == ["time", "reference_mean", "test_mean"]
    assert df["time"].tolist() == TIMES
    assert df["test_mean"].tolist() == TEST


def test_fit_results_to_dataframe(results: dict[str, object]) -> None:
    """DissolutionFitResults.to_dataframe() has one row per model and param_ columns."""
    fit = results["fit"]
    df = fit.to_dataframe()  # type: ignore[attr-defined]
    assert df["model_name"].tolist() == [f.model_name for f in fit.fits]  # type: ignore[attr-defined]
    assert any(col.startswith("param_") for col in df.columns)


def test_multi_media_to_dataframe(results: dict[str, object]) -> None:
    """MultiMediaResult.to_dataframe() has one row per medium in media order."""
    df = results["multi_media"].to_dataframe()  # type: ignore[attr-defined]
    assert df["medium"].tolist() == ["pH 1.2", "pH 6.8"]
    assert df["f2_value"].tolist() == [85.0, 85.0]


def test_alcohol_to_dataframe(results: dict[str, object]) -> None:
    """AlcoholDoseDumpingResult.to_dataframe() has one row per ethanol medium."""
    alcohol = results["alcohol"]
    df = alcohol.to_dataframe()  # type: ignore[attr-defined]
    assert df["ethanol_pct"].tolist() == [20.0, 40.0]
    assert df["f2"].tolist() == list(alcohol.f2_by_ethanol_pct.values())  # type: ignore[attr-defined]


def test_be_result_to_dataframe_is_a_copy(results: dict[str, object]) -> None:
    """BEResult.to_dataframe() returns the subject table without aliasing it."""
    be = results["be"]
    df = be.to_dataframe()  # type: ignore[attr-defined]
    pd.testing.assert_frame_equal(df, be.subjects_df)  # type: ignore[attr-defined]
    df.iloc[0, 0] = "changed"
    assert be.subjects_df.iloc[0, 0] != "changed"  # type: ignore[attr-defined]


def test_formal_be_to_dataframe_is_anova_table(results: dict[str, object]) -> None:
    """FormalBEResult.to_dataframe() returns the ANOVA rows in order."""
    formal = results["formal_be"]
    df = formal.to_dataframe()  # type: ignore[attr-defined]
    assert df["source"].tolist() == [row.source for row in formal.anova]  # type: ignore[attr-defined]
    assert list(df.columns) == [
        "source",
        "df",
        "sum_squares",
        "mean_square",
        "f_value",
        "p_value",
    ]


def test_vpc_to_dataframe(results: dict[str, object]) -> None:
    """VPCResult.to_dataframe() has one row per bin."""
    vpc = results["vpc"]
    df = vpc.to_dataframe()  # type: ignore[attr-defined]
    assert df["bin_mid"].tolist() == list(vpc.bin_mids)  # type: ignore[attr-defined]
    assert df.shape[1] == 7


def test_to_builtin_converts_numpy_and_pandas() -> None:
    """to_builtin() turns NumPy and pandas values into built-in types."""
    value = {
        np.float64(1.5): np.array([1, 2]),
        "s": pd.Series([np.int64(3)]),
        "f": pd.DataFrame({"a": [np.float32(0.5)]}),
        "t": (np.bool_(True), float("nan")),
    }
    out = to_builtin(value)
    assert out[1.5] == [1, 2]
    assert out["s"] == [3]
    assert out["f"] == [{"a": 0.5}]
    assert out["t"][0] is True
    assert np.isnan(out["t"][1])


def test_dataclass_to_dict_skips_private_and_excluded_fields() -> None:
    """Private fields and excluded names are left out."""

    @dataclasses.dataclass
    class Example:
        a: int
        b: int
        _hidden: int

    assert dataclass_to_dict(Example(1, 2, 3), exclude=("b",)) == {"a": 1}


def test_lazy_subpackage_access() -> None:
    """import openpkflow loads no subpackage until one is accessed."""
    code = (
        "import sys, openpkflow\n"
        "assert 'openpkflow.nca' not in sys.modules\n"
        "assert openpkflow.nca.NCAStudy.__name__ == 'NCAStudy'\n"
        "assert 'openpkflow.nca' in sys.modules\n"
        "assert 'be' in dir(openpkflow)\n"
    )
    subprocess.run([sys.executable, "-c", code], check=True)


def test_unknown_attribute_raises() -> None:
    """Names that are not subpackages raise AttributeError."""
    import openpkflow

    with pytest.raises(AttributeError, match="no attribute 'not_a_module'"):
        _ = openpkflow.not_a_module  # type: ignore[attr-defined]
