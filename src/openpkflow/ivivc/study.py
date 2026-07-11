"""High-level IVIVCStudy API."""

from __future__ import annotations

import numpy as np

from .methods import (
    convolution_predict,
    ivivc_predictability,
    levy_plot_data,
    loo_riegelman,
    wagner_nelson,
)
from .results import IVIVCResult


class IVIVCStudy:
    """Orchestrate a full IVIVC Level A analysis.

    Combines deconvolution, convolution prediction, Levy plot, and
    predictability assessment into a single workflow.
    """

    def __init__(
        self,
        *,
        in_vivo_times: list[float] | np.ndarray,
        in_vivo_concs: list[float] | np.ndarray,
        dissolution_times: list[float] | np.ndarray,
        dissolution_pct: list[float] | np.ndarray,
        iv_uir_times: list[float] | np.ndarray,
        iv_uir_concs: list[float] | np.ndarray,
        method: str = "wagner_nelson",
        dose_diss: float | None = None,
        dose_iv: float | None = None,
        kel: float | None = None,
        k12: float | None = None,
        k21: float | None = None,
        study_label: str = "",
        dissolution_time_unit: str = "hours",
    ) -> None:
        """Initialise an IVIVC study.

        Parameters
        ----------
        in_vivo_times : list[float] | np.ndarray
            In vivo plasma sampling times after oral administration (hours).
        in_vivo_concs : list[float] | np.ndarray
            Plasma concentrations at each in vivo time point.
        dissolution_times : list[float] | np.ndarray
            In vitro dissolution time points (see ``dissolution_time_unit``).
        dissolution_pct : list[float] | np.ndarray
            Cumulative percent dissolved at each dissolution time point.
        iv_uir_times : list[float] | np.ndarray
            IV bolus sampling times for unit impulse response (hours).
        iv_uir_concs : list[float] | np.ndarray
            IV bolus plasma concentrations.
        method : str, optional
            Deconvolution method: ``"wagner_nelson"`` or ``"loo_riegelman"``.
        dose_diss : float or None, optional
            Dose for the dissolution formulation unit.
        dose_iv : float or None, optional
            Dose for the IV unit impulse response.
        kel : float or None, optional
            Terminal elimination rate constant (1/h). Required for AUCinf
            extrapolation in predictability; also used by Wagner-Nelson when
            not estimated from UIR. Must not be silently defaulted.
        k12 : float or None, optional
            Central-to-peripheral transfer rate (1/h) for Loo-Riegelman.
        k21 : float or None, optional
            Peripheral-to-central transfer rate (1/h) for Loo-Riegelman.
        study_label : str, optional
            Optional label for this study.
        dissolution_time_unit : {"hours", "minutes"}, optional
            Unit of dissolution times. Minutes are converted to hours for
            convolution and Levy matching. Default ``"hours"``.
        """
        self._in_vivo_times = np.asarray(in_vivo_times, dtype=float)
        self._in_vivo_concs = np.asarray(in_vivo_concs, dtype=float)
        self._diss_times = np.asarray(dissolution_times, dtype=float)
        self._diss_pct = np.asarray(dissolution_pct, dtype=float)
        self._uir_times = np.asarray(iv_uir_times, dtype=float)
        self._uir_concs = np.asarray(iv_uir_concs, dtype=float)
        self._method = method
        self._dose_diss = dose_diss
        self._dose_iv = dose_iv
        self._kel = kel
        self._k12 = k12
        self._k21 = k21
        self._study_label = study_label
        self._diss_time_unit = dissolution_time_unit

    def analyze(self) -> IVIVCResult:
        """Run the complete IVIVC Level A workflow.

        Returns
        -------
        IVIVCResult
            Comprehensive result with deconvolution, convolution, Levy plot,
            and predictability data.

        Raises
        ------
        ValueError
            If the deconvolution method is unknown or if parameter requirements
            are not met.
        """
        iv_t = self._in_vivo_times
        iv_c = self._in_vivo_concs
        diss_t = self._diss_times
        diss_pct = self._diss_pct
        uir_t = self._uir_times
        uir_c = self._uir_concs

        # Step 1: Deconvolution
        if self._method == "wagner_nelson":
            fa = wagner_nelson(
                iv_t,
                iv_c,
                kel=self._kel,
                iv_unit_impulse_times=uir_t,
                iv_unit_impulse_concs=uir_c,
            )
        elif self._method == "loo_riegelman":
            if self._kel is None or self._k12 is None or self._k21 is None:
                raise ValueError("Loo-Riegelman requires kel, k12, and k21 to be specified")
            fa = loo_riegelman(
                iv_t,
                iv_c,
                kel=self._kel,
                k12=self._k12,
                k21=self._k21,
            )
        else:
            raise ValueError(
                f"Unknown deconvolution method {self._method!r}. "
                "Use 'wagner_nelson' or 'loo_riegelman'."
            )

        # Align dissolution times to hours for Levy matching against Fa(t)
        unit = self._diss_time_unit.lower().strip()
        if unit in ("min", "mins", "minute", "minutes"):
            diss_t_h = diss_t / 60.0
        elif unit in ("h", "hr", "hrs", "hour", "hours"):
            diss_t_h = diss_t
        else:
            raise ValueError(
                f"dissolution_time_unit must be 'hours' or 'minutes' "
                f"(got {self._diss_time_unit!r})."
            )

        # Step 2: Levy plot -- match dissolution fraction to in vivo absorption
        # at common times (hours). Levy regression uses fraction dissolved vs
        # fraction absorbed; times are only used for the interpolation grid.
        diss_frac = diss_pct / 100.0
        fa_interp = np.interp(diss_t_h, iv_t, fa, left=0.0, right=min(float(fa[-1]), 1.0))

        levy = levy_plot_data(diss_t_h, diss_frac, fa_interp)

        # Step 3: Convolution prediction (dissolution times converted internally)
        pred_times, pred_concs = convolution_predict(
            diss_t,
            diss_pct,
            iv_unit_impulse_times=uir_t,
            iv_unit_impulse_concs=uir_c,
            dose_diss=self._dose_diss,
            dose_iv=self._dose_iv,
            dissolution_time_unit=self._diss_time_unit,
        )

        # Step 4: Predictability assessment (%PE only; no false FDA verdict)
        obs_cmax = float(np.max(iv_c))
        pred_cmax = float(np.max(pred_concs))

        from .methods import _trapz_linear

        if self._kel is None or self._kel <= 0:
            raise ValueError(
                "kel must be a positive terminal elimination rate (1/h) for "
                "AUCinf extrapolation in predictability assessment. "
                "Silent default kel is not allowed."
            )
        kel = float(self._kel)

        obs_auc_t = _trapz_linear(iv_t, iv_c)
        obs_aucinf = float(obs_auc_t[-1] + iv_c[-1] / kel)

        pred_auc_t = _trapz_linear(pred_times, pred_concs)
        pred_aucinf = float(pred_auc_t[-1] + pred_concs[-1] / kel)

        predictability = ivivc_predictability(
            obs_cmax,
            pred_cmax,
            obs_aucinf,
            pred_aucinf,
        )

        return IVIVCResult(
            method=self._method,
            times=iv_t,
            concentrations=iv_c,
            fa=fa,
            levy_plot=levy,
            ivt_times=diss_t,
            ivt_fraction=diss_frac,
            predicted_times=pred_times,
            predicted_concs=pred_concs,
            predictability=predictability,
            study_label=self._study_label,
        )
