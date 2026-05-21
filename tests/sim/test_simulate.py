"""Tests for simulate() and SimulationResult."""

from __future__ import annotations

import math

import numpy as np
import pytest

from openpkflow.sim.dosing import Dose, DoseRegimen
from openpkflow.sim.models import OneCompartmentModel, TwoCompartmentModel
from openpkflow.sim.simulate import simulate


def _make_times(end: float, n: int = 200) -> list[float]:
    return list(np.linspace(0, end, n))


# ---------------------------------------------------------------------------
# OneCompartmentModel
# ---------------------------------------------------------------------------


class TestSimulate1Cmt:
    """Tests for simulate() with OneCompartmentModel."""

    def test_iv_bolus_single_dose(self) -> None:
        """Single IV bolus: C(0) = D/Vz and decays mono-exponentially."""
        model = OneCompartmentModel(route="iv_bolus", CL=5.0, Vz=20.0)
        regimen = DoseRegimen((Dose(100.0, 0.0, "iv_bolus"),))
        result = simulate(model, regimen, _make_times(24))
        assert math.isclose(result.concs[0], 100.0 / 20.0, rel_tol=1e-10)
        assert result.concs[-1] < result.concs[0]

    def test_iv_infusion_single_dose(self) -> None:
        """Single IV infusion: C(0) = 0, rises during, decays after."""
        model = OneCompartmentModel(route="iv_infusion", CL=5.0, Vz=20.0)
        regimen = DoseRegimen((Dose(100.0, 0.0, "iv_infusion", t_inf=2.0),))
        result = simulate(model, regimen, _make_times(24))
        assert math.isclose(result.concs[0], 0.0, abs_tol=1e-12)
        assert result.Cmax > 0.0
        assert result.Tmax > 0.0

    def test_oral_single_dose(self) -> None:
        """Single oral dose: C(0) = 0, Tmax > 0."""
        model = OneCompartmentModel(route="oral", CL_F=5.0, Vz_F=20.0, ka=1.5)
        regimen = DoseRegimen((Dose(100.0, 0.0, "oral"),))
        result = simulate(model, regimen, _make_times(24))
        assert math.isclose(result.concs[0], 0.0, abs_tol=1e-12)
        assert result.Tmax > 0.0

    def test_repeated_iv_bolus_accumulation(self) -> None:
        """Multiple IV bolus doses accumulate: Cmax after dose 5 > Cmax after dose 1."""
        model = OneCompartmentModel(route="iv_bolus", CL=2.0, Vz=20.0)
        regimen = DoseRegimen.from_repeated(
            amount=50.0, route="iv_bolus", tau=8.0, n_doses=5
        )
        t = list(np.linspace(0, 40, 400))
        result = simulate(model, regimen, t)
        # Conc just after dose 5 (t=32+eps) should exceed conc just after dose 1 (t=eps)
        idx_dose1 = next(i for i, tv in enumerate(result.times) if tv > 0.1)
        idx_dose5 = next(i for i, tv in enumerate(result.times) if tv > 32.1)
        assert result.concs[idx_dose5] > result.concs[idx_dose1]

    def test_route_mismatch_raises(self) -> None:
        """Raises ValueError when model.route != regimen.route."""
        model = OneCompartmentModel(route="iv_bolus", CL=5.0, Vz=20.0)
        regimen = DoseRegimen((Dose(100.0, 0.0, "oral"),))
        with pytest.raises(ValueError, match="does not match"):
            simulate(model, regimen, _make_times(24))

    def test_empty_times_raises(self) -> None:
        """Raises ValueError for empty time array."""
        model = OneCompartmentModel(route="iv_bolus", CL=5.0, Vz=20.0)
        regimen = DoseRegimen((Dose(100.0, 0.0, "iv_bolus"),))
        with pytest.raises(ValueError, match="non-empty"):
            simulate(model, regimen, [])

    def test_pre_dose_warning(self) -> None:
        """Warns when simulation starts before first dose."""
        model = OneCompartmentModel(route="iv_bolus", CL=5.0, Vz=20.0)
        regimen = DoseRegimen((Dose(100.0, 2.0, "iv_bolus"),))
        result = simulate(model, regimen, _make_times(24))
        assert any(
            "pre-dose" in w.lower() or "before first dose" in w.lower()
            for w in result.warnings
        )

    def test_half_life_matches_model(self) -> None:
        """Simulated half-life matches model's half_life property."""
        CL, Vz = 10.0, 50.0
        model = OneCompartmentModel(route="iv_bolus", CL=CL, Vz=Vz)
        regimen = DoseRegimen((Dose(500.0, 0.0, "iv_bolus"),))
        t = list(np.linspace(0, 48, 1000))
        result = simulate(model, regimen, t)
        t_half = model.half_life
        C0 = result.concs[0]
        # Find index closest to t = t_half
        idx = min(range(len(result.times)), key=lambda i: abs(result.times[i] - t_half))
        assert math.isclose(result.concs[idx], C0 / 2.0, rel_tol=0.01)


# ---------------------------------------------------------------------------
# TwoCompartmentModel
# ---------------------------------------------------------------------------


class TestSimulate2Cmt:
    """Tests for simulate() with TwoCompartmentModel."""

    def test_iv_bolus_c0(self) -> None:
        """2-cmt IV bolus: C(0) = D/V1."""
        model = TwoCompartmentModel(route="iv_bolus", CL=5.0, V1=20.0, Q=3.0, V2=15.0)
        regimen = DoseRegimen((Dose(100.0, 0.0, "iv_bolus"),))
        result = simulate(model, regimen, _make_times(24))
        assert math.isclose(result.concs[0], 100.0 / 20.0, rel_tol=1e-10)

    def test_oral_c0_is_zero(self) -> None:
        """2-cmt oral: C(0) = 0."""
        model = TwoCompartmentModel(route="oral", CL_F=5.0, V1_F=20.0, Q=3.0, V2=15.0, ka=1.5)
        regimen = DoseRegimen((Dose(100.0, 0.0, "oral"),))
        result = simulate(model, regimen, _make_times(24))
        assert math.isclose(result.concs[0], 0.0, abs_tol=1e-12)

    def test_iv_infusion_c0_is_zero(self) -> None:
        """2-cmt IV infusion: C(0) = 0, rises during, decays after."""
        model = TwoCompartmentModel(route="iv_infusion", CL=5.0, V1=20.0, Q=3.0, V2=15.0)
        regimen = DoseRegimen((Dose(100.0, 0.0, "iv_infusion", t_inf=2.0),))
        result = simulate(model, regimen, _make_times(24))
        assert math.isclose(result.concs[0], 0.0, abs_tol=1e-12)
        assert result.Cmax > 0.0

    def test_iv_infusion_dose_requires_t_inf(self) -> None:
        """Dose validation: iv_infusion route requires t_inf > 0."""
        with pytest.raises(ValueError, match="t_inf"):
            Dose(100.0, 0.0, "iv_infusion")

    def test_biexponential_decline_faster_initially(self) -> None:
        """2-cmt IV bolus shows faster initial decline than terminal (biexponential)."""
        model = TwoCompartmentModel(route="iv_bolus", CL=2.0, V1=10.0, Q=5.0, V2=40.0)
        regimen = DoseRegimen((Dose(100.0, 0.0, "iv_bolus"),))
        t = list(np.linspace(0.01, 24, 500))
        result = simulate(model, regimen, t)
        # Compute log-slopes at early and late time points
        c = np.array(result.concs)
        t_arr = np.array(result.times)
        slope_early = (np.log(c[1]) - np.log(c[0])) / (t_arr[1] - t_arr[0])
        slope_late = (np.log(c[-1]) - np.log(c[-10])) / (t_arr[-1] - t_arr[-10])
        # Early slope should be steeper (more negative)
        assert slope_early < slope_late


# ---------------------------------------------------------------------------
# SimulationResult helpers
# ---------------------------------------------------------------------------


class TestSimulationResult:
    """Tests for SimulationResult methods."""

    def _oral_result(self):
        model = OneCompartmentModel(route="oral", CL_F=5.0, Vz_F=20.0, ka=1.5)
        regimen = DoseRegimen((Dose(100.0, 0.0, "oral"),))
        return simulate(model, regimen, list(np.linspace(0, 24, 200)))

    def test_summary_is_str(self) -> None:
        r = self._oral_result()
        s = r.summary()
        assert isinstance(s, str)
        assert "Cmax" in s

    def test_to_dataframe_columns(self) -> None:
        r = self._oral_result()
        df = r.to_dataframe()
        assert list(df.columns) == ["time", "conc"]
        assert len(df) == 200

    def test_to_dict_keys(self) -> None:
        r = self._oral_result()
        d = r.to_dict()
        assert "Cmax" in d and "Tmax" in d and "model" in d

    def test_cmax_tmax_consistent(self) -> None:
        r = self._oral_result()
        expected_cmax = max(r.concs)
        expected_tmax = r.times[r.concs.index(expected_cmax)]
        assert math.isclose(r.Cmax, expected_cmax, rel_tol=1e-12)
        assert math.isclose(r.Tmax, expected_tmax, rel_tol=1e-12)

    def test_report_html_returns_str(self, tmp_path) -> None:
        r = self._oral_result()
        out = tmp_path / "sim_report.html"
        content = r.report(str(out), format="html")
        assert isinstance(content, str)
        assert out.exists()
        assert "OpenPKFlow" in content

    def test_report_markdown_returns_str(self, tmp_path) -> None:
        r = self._oral_result()
        out = tmp_path / "sim_report.md"
        content = r.report(str(out), format="markdown")
        assert isinstance(content, str)
        assert "Cmax" in content

    def test_plot_returns_nonempty_base64(self) -> None:
        r = self._oral_result()
        b64 = r.plot()
        assert isinstance(b64, str)
        assert len(b64) > 100
