"""SimulationResult dataclass for PK simulation output."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pandas as pd

    from openpkflow.sim.dosing import DoseRegimen
    from openpkflow.sim.models import OneCompartmentModel, TwoCompartmentModel


@dataclass
class SimulationResult:
    """Output of a single PK simulation run.

    Parameters
    ----------
    times : list[float]
        Simulation time grid.
    concs : list[float]
        Simulated central compartment concentrations.
    model : OneCompartmentModel or TwoCompartmentModel
        PK model used in this simulation.
    regimen : DoseRegimen
        Dosing regimen used in this simulation.
    label : str, optional
        Descriptive label for this run.
    warnings : list[str], optional
        Warnings generated during simulation.
    """

    times: list[float]
    concs: list[float]
    model: OneCompartmentModel | TwoCompartmentModel
    regimen: DoseRegimen
    label: str = ""
    warnings: list[str] = field(default_factory=list)

    # Derived summary (computed on first access via summary())
    _Cmax: float | None = field(default=None, init=False, repr=False)
    _Tmax: float | None = field(default=None, init=False, repr=False)

    def _compute_summary_stats(self) -> None:
        if self._Cmax is None:
            import numpy as np

            c = np.array(self.concs)
            t = np.array(self.times)
            idx = int(np.argmax(c))
            self._Cmax = float(c[idx])
            self._Tmax = float(t[idx])

    @property
    def Cmax(self) -> float:
        """Maximum simulated concentration."""
        self._compute_summary_stats()
        assert self._Cmax is not None
        return self._Cmax

    @property
    def Tmax(self) -> float:
        """Time of maximum simulated concentration."""
        self._compute_summary_stats()
        assert self._Tmax is not None
        return self._Tmax

    def summary(self) -> str:
        """Return an ASCII-only plain-text summary of the simulation.

        Returns
        -------
        str
            Multi-line summary with model, regimen, and key PK metrics.
        """
        model_name = type(self.model).__name__
        n_doses = len(self.regimen.doses)
        route = self.regimen.route

        lines = [
            "PK Simulation Summary",
            "=====================",
            f"Label      : {self.label or 'N/A'}",
            f"Model      : {model_name}",
            f"Route      : {route}",
            f"N doses    : {n_doses}",
            f"Time range : {self.times[0]:.4g} -- {self.times[-1]:.4g}",
            "",
            "Model Parameters",
            "----------------",
        ]
        for k, v in self.model.param_dict().items():
            if isinstance(v, float):
                lines.append(f"  {k:<12}: {v:.4g}")
            else:
                lines.append(f"  {k:<12}: {v}")

        lines += [
            "",
            "Simulation Results",
            "------------------",
            f"Cmax : {self.Cmax:.4g}",
            f"Tmax : {self.Tmax:.4g}",
            f"Cmin : {min(self.concs):.4g}",
            f"Clast: {self.concs[-1]:.4g}",
        ]

        if self.warnings:
            lines += ["", "Warnings", "--------"]
            for w in self.warnings:
                lines.append(f"  - {w}")

        return "\n".join(lines)

    def to_dataframe(self) -> pd.DataFrame:
        """Return a DataFrame with columns time and conc.

        Returns
        -------
        pd.DataFrame
            One row per time point.
        """
        import pandas as pd

        return pd.DataFrame({"time": self.times, "conc": self.concs})

    def to_dict(self) -> dict[str, Any]:
        """Return a flat dict of scalar summary values.

        Returns
        -------
        dict[str, Any]
            Label, model type, route, n_doses, Cmax, Tmax, and warnings.
        """
        return {
            "label": self.label,
            "model": type(self.model).__name__,
            "route": self.regimen.route,
            "n_doses": len(self.regimen.doses),
            "t_start": self.times[0],
            "t_end": self.times[-1],
            "Cmax": self.Cmax,
            "Tmax": self.Tmax,
            "Cmin": min(self.concs),
            "Clast": self.concs[-1],
            "warnings": self.warnings,
        }

    def plot(
        self,
        *,
        time_unit: str = "h",
        conc_unit: str = "ng/mL",
    ) -> str:
        """Return a base64-encoded PNG concentration-time plot.

        Parameters
        ----------
        time_unit : str, optional
            Time axis unit label, by default "h".
        conc_unit : str, optional
            Concentration axis unit label, by default "ng/mL".

        Returns
        -------
        str
            Base64-encoded PNG string (usable as HTML img src).
        """
        from openpkflow.sim.plotting import pk_profile_plot_b64

        return pk_profile_plot_b64(
            times=self.times,
            concs=self.concs,
            dose_times=self.regimen.dose_times,
            label=self.label,
            time_unit=time_unit,
            conc_unit=conc_unit,
        )

    def report(
        self,
        output_path: str | Path,
        *,
        format: str = "html",
        time_unit: str = "h",
        conc_unit: str = "ng/mL",
    ) -> str | bytes:
        """Generate a PK simulation report.

        Parameters
        ----------
        output_path : str | Path
            Where to save the report file.
        format : str, optional
            Output format: "html", "markdown", "pdf", or "docx".
            Defaults to "html". PDF and DOCX require openpkflow[reports].
        time_unit : str, optional
            Time unit label for plots and tables, by default "h".
        conc_unit : str, optional
            Concentration unit label for plots and tables, by default "ng/mL".

        Returns
        -------
        str | bytes
            Rendered report content (str for html/markdown, bytes for pdf/docx).
        """
        from openpkflow.sim.reporting import report_simulation

        return report_simulation(
            self,
            output_path=output_path,
            format=format,
            time_unit=time_unit,
            conc_unit=conc_unit,
        )
