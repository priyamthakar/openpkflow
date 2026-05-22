"""High-level NCAStudy API for running non-compartmental analysis."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import pandas as pd

from openpkflow.nca.methods import (
    AUCResult,
    LambdaZResult,
    auc_inf_obs,
    auc_linear,
    auc_linear_up_log_down,
    auc_log,
    auc_percent_extrapolated,
    clearance_volume_parameters,
    cmax,
    cumulative_urinary_excretion,
    lambda_z,
    percent_excreted,
    renal_clearance,
    steady_state_parameters,
    tmax,
)
from openpkflow.nca.results import NCAResult, NCASummaryResults

_VALID_AUC_METHODS = ("linear", "log", "linear_up_log_down")


class NCAStudy:
    """Non-compartmental analysis study object.

    Load PK concentration-time data, run NCA per subject, and generate reports.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        *,
        auc_method: Literal["linear", "log", "linear_up_log_down"],
        blq_method: str,
        subject_col: str = "subject",
        time_col: str = "time",
        conc_col: str = "conc",
        dose_col: str = "dose",
        route_col: str = "route",
        lloq: float | None = None,
        steady_state: bool = False,
        tau: float | None = None,
        urine_volume_col: str | None = None,
        urine_conc_col: str | None = None,
    ) -> None:
        """Initialise an NCAStudy from a validated DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            Concentration-time data with subject, time, conc, dose, and route columns.
        auc_method : {"linear", "log", "linear_up_log_down"}
            AUC calculation method.
        blq_method : str
            BLQ handling method identifier (stored for reporting; caller is responsible
            for applying BLQ handling before passing data).
        subject_col : str, optional
            Column name for subject identifiers. Default ``"subject"``.
        time_col : str, optional
            Column name for sample times. Default ``"time"``.
        conc_col : str, optional
            Column name for observed concentrations. Default ``"conc"``.
        dose_col : str, optional
            Column name for dose. Default ``"dose"``.
        route_col : str, optional
            Column name for route of administration. Default ``"route"``.
        lloq : float or None, optional
            Lower limit of quantification. Reserved for future BLQ handling. Default None.
        steady_state : bool, optional
            If True, compute steady-state parameters (AUCtau, Cmax_ss, Cmin_ss,
            fluctuation, swing). Requires tau. Default False.
        tau : float or None, optional
            Dosing interval length for steady-state analysis. Required if
            steady_state is True.
        urine_volume_col : str or None, optional
            Column name for urine volume if urinary excretion parameters are needed.
        urine_conc_col : str or None, optional
            Column name for urine concentration if urinary excretion parameters are needed.

        Raises
        ------
        ValueError
            If auc_method is not one of the valid choices, or steady_state is True
            but tau is not provided.
        """
        if auc_method not in _VALID_AUC_METHODS:
            raise ValueError(
                f"auc_method must be one of {_VALID_AUC_METHODS!r} (got {auc_method!r})."
            )
        if steady_state and tau is None:
            raise ValueError(
                "tau is required when steady_state=True for computing"
                " steady-state parameters (AUCtau, Cmax_ss, Cmin_ss, etc.)."
            )
        self._df = df
        self._auc_method = auc_method
        self._blq_method = blq_method
        self._subject_col = subject_col
        self._time_col = time_col
        self._conc_col = conc_col
        self._dose_col = dose_col
        self._route_col = route_col
        self._lloq = lloq
        self._steady_state = steady_state
        self._tau = tau
        self._urine_volume_col = urine_volume_col
        self._urine_conc_col = urine_conc_col

    @classmethod
    def from_csv(
        cls,
        path: str | Path,
        *,
        auc_method: Literal["linear", "log", "linear_up_log_down"],
        blq_method: str,
        subject_col: str = "subject",
        time_col: str = "time",
        conc_col: str = "conc",
        dose_col: str = "dose",
        route_col: str = "route",
        lloq: float | None = None,
        steady_state: bool = False,
        tau: float | None = None,
        urine_volume_col: str | None = None,
        urine_conc_col: str | None = None,
    ) -> NCAStudy:
        """Load an NCAStudy from a CSV file.

        Parameters
        ----------
        path : str | Path
            Path to the NCA CSV file.
        auc_method : {"linear", "log", "linear_up_log_down"}
            AUC calculation method.
        blq_method : str
            BLQ handling method identifier.
        subject_col : str, optional
            Column name for subject identifiers. Default ``"subject"``.
        time_col : str, optional
            Column name for sample times. Default ``"time"``.
        conc_col : str, optional
            Column name for observed concentrations. Default ``"conc"``.
        dose_col : str, optional
            Column name for dose. Default ``"dose"``.
        route_col : str, optional
            Column name for route of administration. Default ``"route"``.
        lloq : float or None, optional
            Lower limit of quantification. Default None.
        steady_state : bool, optional
            If True, compute steady-state parameters. Requires tau.
        tau : float or None, optional
            Dosing interval length for steady-state analysis.
        urine_volume_col : str or None, optional
            Column name for urine volume.
        urine_conc_col : str or None, optional
            Column name for urine concentration.

        Returns
        -------
        NCAStudy
            Loaded and validated study object.

        Raises
        ------
        FileNotFoundError
            If the CSV file does not exist.
        ValueError
            If required columns are missing, data fails validation, or auc_method is invalid.
        """
        from openpkflow.nca.loader import load_nca_csv

        df = load_nca_csv(
            path,
            subject_col=subject_col,
            time_col=time_col,
            conc_col=conc_col,
            dose_col=dose_col,
            route_col=route_col,
            blq_method=blq_method,
            lloq=lloq,
        )
        return cls(
            df,
            auc_method=auc_method,
            blq_method=blq_method,
            subject_col=subject_col,
            time_col=time_col,
            conc_col=conc_col,
            dose_col=dose_col,
            route_col=route_col,
            lloq=lloq,
            steady_state=steady_state,
            tau=tau,
            urine_volume_col=urine_volume_col,
            urine_conc_col=urine_conc_col,
        )

    def analyze(self) -> NCASummaryResults:
        """Run NCA for every subject in the dataset.

        Returns
        -------
        NCASummaryResults
            Collection of per-subject NCAResult objects.
        """
        results: list[NCAResult] = []

        for subject, group in self._df.groupby(self._subject_col, sort=True):
            group_sorted = group.sort_values(self._time_col)

            t: list[float] = group_sorted[self._time_col].tolist()
            c: list[float] = group_sorted[self._conc_col].tolist()
            dose: float = float(group_sorted[self._dose_col].dropna().iloc[0])
            route: str = str(group_sorted[self._route_col].iloc[0])

            subject_str = str(subject)
            nca_warnings: list[str] = []

            # Cmax and Tmax
            cmax_val = cmax(c)
            tmax_val = tmax(t, c)

            # AUClast via dispatch
            if self._auc_method == "linear":
                auclast_val: float = auc_linear(t, c)
                auc_warnings: list[str] = []
            else:
                fn = auc_log if self._auc_method == "log" else auc_linear_up_log_down
                res: AUCResult = fn(t, c)
                auclast_val = res.value
                auc_warnings = res.warnings

            nca_warnings.extend(auc_warnings)

            # Terminal elimination rate constant
            lz_result: LambdaZResult | None = None
            aucinf: float | None = None
            pct_extrap: float | None = None
            cl_params: dict[str, float] | None = None

            try:
                lz_result = lambda_z(t, c, method="auto")
                nca_warnings.extend(lz_result.warnings)

                # Last quantifiable concentration (last positive value)
                clast_obs: float = 0.0
                for cv in reversed(c):
                    if cv > 0.0:
                        clast_obs = cv
                        break

                aucinf = auc_inf_obs(auclast_val, clast_obs, lz_result)
                pct_extrap = auc_percent_extrapolated(auclast_val, aucinf)
                cl_params = clearance_volume_parameters(dose, aucinf, lz_result, route=route)

            except ValueError as exc:
                nca_warnings.append(f"lambda_z could not be estimated: {exc}")

            # Route-specific clearance/volume population
            cl_f: float | None = None
            vz_f: float | None = None
            cl: float | None = None
            vz: float | None = None

            if cl_params is not None:
                if route == "oral":
                    cl_f = cl_params.get("CL_F")
                    vz_f = cl_params.get("Vz_F")
                else:
                    cl = cl_params.get("CL")
                    vz = cl_params.get("Vz")

            # %AUCextrap FDA flag (>20% criterion)
            if pct_extrap is not None and pct_extrap > 20.0:
                nca_warnings.append(
                    f"%AUCextrap = {pct_extrap:.1f}% exceeds FDA 20% threshold. "
                    "The estimate may be unreliable; consider extending the sampling schedule."
                )

            # Dose-normalised parameters
            dn_auclast = auclast_val / dose if dose > 0 else None
            dn_aucinf = aucinf / dose if aucinf is not None and dose > 0 else None
            dn_cmax = cmax_val / dose if dose > 0 else None

            # Lambda_z quality metrics
            lz_adj_r2 = lz_result.adj_r_squared if lz_result is not None else None
            lz_n_points = lz_result.n_points if lz_result is not None else None

            # Steady-state parameters
            cmax_ss: float | None = None
            cmin_ss: float | None = None
            cavg_ss: float | None = None
            auctau: float | None = None
            fluct_pct: float | None = None
            swing: float | None = None
            accum_ratio: float | None = None

            if self._steady_state and self._tau is not None:
                ss_params = steady_state_parameters(
                    t, c, tau=self._tau, auc_method=self._auc_method
                )
                cmax_ss = ss_params["Cmax_ss"]
                cmin_ss = ss_params["Cmin_ss"]
                cavg_ss = ss_params["Cavg_ss"]
                auctau = ss_params["AUCtau"]
                fluct_pct = ss_params["fluctuation_pct"]
                swing = ss_params["swing"]
                accum_ratio = ss_params["accumulation_ratio"]

            # Urinary excretion parameters
            ae: float | None = None
            ae_pct: float | None = None
            clr: float | None = None

            if self._urine_volume_col is not None and self._urine_conc_col is not None:
                has_urine = (
                    self._urine_volume_col in group_sorted.columns
                    and self._urine_conc_col in group_sorted.columns
                )
                if has_urine:
                    u_vol = group_sorted[self._urine_volume_col].tolist()
                    u_conc = group_sorted[self._urine_conc_col].tolist()
                    try:
                        cum_ae = cumulative_urinary_excretion(t, u_vol, u_conc)
                        ae = float(cum_ae[-1]) if len(cum_ae) > 0 else 0.0
                        ae_pct = percent_excreted(ae, dose) if ae is not None else None
                        if aucinf is not None and aucinf > 0:
                            clr = renal_clearance(ae, aucinf)
                    except ValueError:
                        pass

            result = NCAResult(
                subject=subject_str,
                route=route,
                dose=dose,
                auc_method=self._auc_method,
                blq_method=self._blq_method,
                AUClast=auclast_val,
                AUCinf_obs=aucinf,
                AUC_percent_extrapolated=pct_extrap,
                Cmax=cmax_val,
                Tmax=tmax_val,
                lambda_z=lz_result.lambda_z if lz_result is not None else None,
                half_life=lz_result.half_life if lz_result is not None else None,
                lambda_z_method=lz_result.method if lz_result is not None else None,
                selected_lambda_z_times=lz_result.selected_times if lz_result is not None else [],
                selected_lambda_z_concs=lz_result.selected_concs if lz_result is not None else [],
                CL_F=cl_f,
                Vz_F=vz_f,
                CL=cl,
                Vz=vz,
                lambda_z_adj_r2=lz_adj_r2,
                lambda_z_n_points=lz_n_points,
                DN_AUClast=dn_auclast,
                DN_AUCinf_obs=dn_aucinf,
                DN_Cmax=dn_cmax,
                Cmax_ss=cmax_ss,
                Cmin_ss=cmin_ss,
                Cavg_ss=cavg_ss,
                AUCtau=auctau,
                fluctuation_pct=fluct_pct,
                swing=swing,
                accumulation_ratio=accum_ratio,
                Ae=ae,
                Ae_pct=ae_pct,
                CLr=clr,
                warnings=nca_warnings,
            )
            results.append(result)

        return NCASummaryResults(
            results=results,
            auc_method=self._auc_method,
            blq_method=self._blq_method,
        )
