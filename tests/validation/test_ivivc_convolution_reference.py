"""IVIVC convolution and Levy plot external reference validation.

Constructs a known analytical case: zero-order dissolution (constant input rate)
convolved with a one-compartment IV bolus unit impulse response (monoexponential
decay).  The convolution integral has a closed form, which is used as the
primary reference.  A second independent high-precision discrete implementation
(fine-grid Riemann sum; not the package source) cross-checks the same case.

References
----------
FDA Guidance for Industry: Extended Release Oral Dosage Forms: Development,
  Evaluation, and Application of In Vitro/In Vivo Correlations (1997), CDER.
  Level A IVIVC uses deconvolution / convolution of dissolution input rate
  with the unit impulse response (UIR).

Gibaldi M, Perrier D (1982). Pharmacokinetics, 2nd ed. Marcel Dekker.
  Convolution of input rate with disposition (UIR); zero-order input into
  one-compartment disposition.  See also Bateman / linear systems PK.

Mathematical definition of the convolution integral (standard analysis)::

    C_pred(t) = (dose_diss / dose_iv) * integral_0^t R_in(tau) * UIR(t - tau) dtau

  where R_in is the dissolution input rate (dF/dt of cumulative fraction
  dissolved) and UIR is the unit impulse response from IV bolus data.

Closed form used here (zero-order fraction rate k = 1/T over [0, T], monoexponential
UIR = C0 * exp(-kel * t))::

    C(t) = (k * C0 / kel) * (exp(-kel * (t - a)) - exp(-kel * t))
    with a = min(t, T)

Levy plot: FDA ER IVIVC (1997) Level A correlation of in vitro fraction dissolved
vs in vivo fraction absorbed at matched times.
"""

from __future__ import annotations

import numpy as np
import pytest

from openpkflow.ivivc.methods import convolution_predict, levy_plot_data

# ---------------------------------------------------------------------------
# Analytical case parameters (1-cmt IV bolus UIR + zero-order input)
# ---------------------------------------------------------------------------

_KEL = 0.25  # 1/h
_C0 = 10.0  # concentration units (Dose_iv / V)
_T_DISS = 4.0  # h; complete zero-order release window
_T_END = 16.0  # h
_K_IN = 1.0 / _T_DISS  # fraction / h
_STEP = 0.02  # h; dense grid so package dt is fine enough for tight tolerance


def _zero_order_dissolution(step: float = _STEP) -> tuple[np.ndarray, np.ndarray]:
    """Cumulative percent dissolved for zero-order release over [0, T_DISS]."""
    d_t = np.arange(0.0, _T_DISS + 1e-12, step)
    d_pct = 100.0 * (d_t / _T_DISS)
    return d_t, d_pct


def _monoexponential_uir(step: float = _STEP) -> tuple[np.ndarray, np.ndarray]:
    """1-cmt IV bolus UIR: C(t) = C0 * exp(-kel * t)."""
    u_t = np.arange(0.0, _T_END + 1e-12, step)
    u_c = _C0 * np.exp(-_KEL * u_t)
    return u_t, u_c


def _closed_form_c(t: np.ndarray | float) -> np.ndarray:
    """Closed-form convolution of constant R_in=k on [0,T] with C0*exp(-kel*t).

    Gibaldi & Perrier (1982) linear systems / zero-order input into 1-cmt
    disposition.  For t > 0 and a = min(t, T)::

        C(t) = (k * C0 / kel) * (exp(-kel*(t-a)) - exp(-kel*t))
    """
    t_arr = np.asarray(t, dtype=float)
    out = np.zeros_like(t_arr, dtype=float)
    pos = t_arr > 0.0
    a = np.minimum(t_arr[pos], _T_DISS)
    out[pos] = (_K_IN * _C0 / _KEL) * (
        np.exp(-_KEL * (t_arr[pos] - a)) - np.exp(-_KEL * t_arr[pos])
    )
    return out


def _independent_high_precision_convolution(
    pred_times: np.ndarray,
    *,
    dt_ref: float = 5e-4,
) -> np.ndarray:
    """Independent fine-grid discrete convolution (not openpkflow source).

    Uses exact analytical input rate (constant k on [0, T)) and exact
    monoexponential UIR on a fine uniform grid, then samples at pred_times.
    """
    t_ref = np.arange(0.0, _T_END + 1e-12, dt_ref)
    r_in = np.where(t_ref < _T_DISS, _K_IN, 0.0)
    uir = _C0 * np.exp(-_KEL * t_ref)
    # Riemann (left) convolution sum; independent of package implementation
    conv_full = np.convolve(r_in, uir, mode="full")[: len(t_ref)] * dt_ref
    return np.interp(pred_times, t_ref, conv_full)


class TestConvolutionClosedFormReference:
    """Match convolution_predict to closed-form and independent discrete refs.

    FDA Guidance for Industry: Extended Release Oral Dosage Forms: Development,
    Evaluation, and Application of In Vitro/In Vivo Correlations (1997), CDER.

    Gibaldi M, Perrier D (1982). Pharmacokinetics, 2nd ed. Marcel Dekker.
    """

    @pytest.fixture(scope="class")
    def predicted(self) -> tuple[np.ndarray, np.ndarray]:
        d_t, d_pct = _zero_order_dissolution()
        u_t, u_c = _monoexponential_uir()
        return convolution_predict(
            d_t,
            d_pct,
            iv_unit_impulse_times=u_t,
            iv_unit_impulse_concs=u_c,
        )

    def test_matches_closed_form_bulk_concentrations(
        self,
        predicted: tuple[np.ndarray, np.ndarray],
    ) -> None:
        """Bulk C(t) agrees with closed form within 5% relative (numerical grid).

        Reference: FDA ER IVIVC (1997); Gibaldi & Perrier (1982) zero-order
        input into 1-cmt disposition closed form.
        """
        pred_t, pred_c = predicted
        c_ref = _closed_form_c(pred_t)
        # Exclude early gradient edge and far tail where C is tiny
        mask = (pred_t >= 1.0) & (pred_t <= 12.0) & (c_ref > 0.05)
        rel = np.abs(pred_c[mask] - c_ref[mask]) / c_ref[mask]
        assert float(np.max(rel)) < 0.05
        assert float(np.median(rel)) < 0.01

    def test_matches_closed_form_cmax(
        self,
        predicted: tuple[np.ndarray, np.ndarray],
    ) -> None:
        """Cmax agrees with closed form within 1% relative.

        Reference: FDA ER IVIVC (1997) predictability metrics use Cmax;
        closed form from Gibaldi & Perrier (1982).
        """
        _, pred_c = predicted
        # Evaluate closed form on a fine independent grid for true Cmax
        t_fine = np.linspace(0.0, _T_END, 5001)
        c_fine = _closed_form_c(t_fine)
        cmax_ref = float(np.max(c_fine))
        cmax_pred = float(np.max(pred_c))
        assert cmax_pred == pytest.approx(cmax_ref, rel=0.01)

    def test_matches_closed_form_auc(
        self,
        predicted: tuple[np.ndarray, np.ndarray],
    ) -> None:
        """AUClast of predicted profile agrees with closed form within 2%.

        For complete absorption (F=1) and linear 1-cmt disposition,
        AUCinf = C0 / kel = Dose/CL (Gibaldi & Perrier, 1982).
        """
        pred_t, pred_c = predicted
        c_ref = _closed_form_c(pred_t)
        auc_pred = float(np.trapezoid(pred_c, pred_t))
        auc_ref = float(np.trapezoid(c_ref, pred_t))
        assert auc_pred == pytest.approx(auc_ref, rel=0.02)
        # Truncated profile AUC should approach Dose/CL = C0/kel
        auc_inf_true = _C0 / _KEL
        assert auc_pred == pytest.approx(auc_inf_true, rel=0.05)

    def test_matches_independent_high_precision_discrete(
        self,
        predicted: tuple[np.ndarray, np.ndarray],
    ) -> None:
        """Agrees with independent fine-grid Riemann convolution within 5% rel.

        Independent implementation uses exact R_in and UIR on dt=5e-4 h grid;
        does not call or copy openpkflow convolution source.
        Reference: convolution definition, FDA ER IVIVC (1997).
        """
        pred_t, pred_c = predicted
        c_hi = _independent_high_precision_convolution(pred_t)
        mask = (pred_t >= 1.0) & (pred_t <= 12.0) & (c_hi > 0.05)
        rel = np.abs(pred_c[mask] - c_hi[mask]) / c_hi[mask]
        assert float(np.max(rel)) < 0.05
        assert float(np.median(rel)) < 0.01

    def test_non_negative_and_finite(
        self,
        predicted: tuple[np.ndarray, np.ndarray],
    ) -> None:
        """Predicted concentrations are finite and non-negative.

        Reference: FDA ER IVIVC (1997) - plasma concentrations must be physical.
        """
        pred_t, pred_c = predicted
        assert len(pred_t) == len(pred_c)
        assert np.all(np.isfinite(pred_c))
        assert np.all(pred_c >= -1e-10)

    def test_dose_ratio_scales_linearly(self) -> None:
        """dose_diss/dose_iv scales C_pred linearly (linear systems PK).

        Reference: Gibaldi & Perrier (1982) - linear superposition.
        """
        d_t, d_pct = _zero_order_dissolution()
        u_t, u_c = _monoexponential_uir()
        _, c1 = convolution_predict(
            d_t,
            d_pct,
            iv_unit_impulse_times=u_t,
            iv_unit_impulse_concs=u_c,
            dose_diss=100.0,
            dose_iv=100.0,
        )
        _, c2 = convolution_predict(
            d_t,
            d_pct,
            iv_unit_impulse_times=u_t,
            iv_unit_impulse_concs=u_c,
            dose_diss=200.0,
            dose_iv=100.0,
        )
        assert float(np.max(c2)) == pytest.approx(2.0 * float(np.max(c1)), rel=0.01)


class TestLevyPlotDegenerateCorrelation:
    """Levy plot linear correlation degenerate cases.

    FDA Guidance for Industry: Extended Release Oral Dosage Forms: Development,
    Evaluation, and Application of In Vitro/In Vivo Correlations (1997), CDER.
    Level A IVIVC Levy plot: F_in_vitro vs F_in_vivo at matched times.
    """

    def test_perfect_one_to_one_correlation(self) -> None:
        """When F_vitro == F_vivo, slope=1, intercept=0, R^2=1.

        Degenerate property of linear regression on identical series.
        Reference: FDA ER IVIVC (1997) Level A correlation concept.
        """
        # Points strictly inside (0.05, 0.95) so levy_plot_data robust mask keeps all
        f = np.array([0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90])
        times = np.arange(len(f), dtype=float)
        result = levy_plot_data(times, f, f)
        assert result["slope"] == pytest.approx(1.0, abs=1e-12)
        assert result["intercept"] == pytest.approx(0.0, abs=1e-12)
        assert result["r_squared"] == pytest.approx(1.0, abs=1e-12)
        assert np.allclose(result["residuals"], 0.0, atol=1e-12)

    def test_perfect_linear_scaled_correlation(self) -> None:
        """Perfect linear F_vivo = 0.8 * F_vitro recovers slope 0.8, R^2=1.

        Reference: FDA ER IVIVC (1997) - linear Level A correlation model.
        """
        f_vitro = np.array([0.10, 0.25, 0.40, 0.55, 0.70, 0.85])
        f_vivo = 0.8 * f_vitro
        times = np.arange(len(f_vitro), dtype=float)
        result = levy_plot_data(times, f_vitro, f_vivo)
        assert result["slope"] == pytest.approx(0.8, abs=1e-12)
        assert result["intercept"] == pytest.approx(0.0, abs=1e-12)
        assert result["r_squared"] == pytest.approx(1.0, abs=1e-12)
