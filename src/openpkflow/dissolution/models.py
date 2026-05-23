"""Dissolution release model fitting — five standard pharmacokinetic release models.

Fits mean dissolution profiles using scipy.optimize.curve_fit.
Models are ranked by AICc (small-sample corrected AIC).

Reference:
    Costa P, Lobo JMS (2001) Modeling and comparison of dissolution profiles.
    Eur J Pharm Sci, 13(2):123-133.
    https://doi.org/10.1016/S0928-0987(01)00095-1
"""

from __future__ import annotations

import math
import warnings
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.optimize import OptimizeWarning, curve_fit

# ──────────────────────────────────────────────────────────────────────────────
# Model callables
# ──────────────────────────────────────────────────────────────────────────────


def _zero_order(t: np.ndarray, k0: float) -> np.ndarray:
    return k0 * t


def _first_order(t: np.ndarray, k1: float) -> np.ndarray:
    return 100.0 * (1.0 - np.exp(-k1 * t))


def _higuchi(t: np.ndarray, kH: float) -> np.ndarray:
    return np.asarray(kH * np.sqrt(t), dtype=float)


def _korsmeyer_peppas(t: np.ndarray, k: float, n: float) -> np.ndarray:
    return np.asarray(k * np.power(np.clip(t, 0.0, None), n), dtype=float)


def _weibull(t: np.ndarray, alpha: float, beta: float) -> np.ndarray:
    return np.asarray(
        100.0 * (1.0 - np.exp(-np.power(np.clip(t, 0.0, None) / beta, alpha))), dtype=float
    )


# ──────────────────────────────────────────────────────────────────────────────
# Per-model initial-guess + bounds helpers
# Each returns (p0: list[float], (lower_bounds, upper_bounds))
# ──────────────────────────────────────────────────────────────────────────────


def _p0_bounds_zero_order(
    t: np.ndarray, Q: np.ndarray
) -> tuple[list[float], tuple[list[float], list[float]]]:
    k0 = float(Q[-1]) / max(float(t[-1]), 1e-9)
    return [k0], ([0.0], [np.inf])


def _p0_bounds_first_order(
    t: np.ndarray, Q: np.ndarray
) -> tuple[list[float], tuple[list[float], list[float]]]:
    q_max = min(float(Q.max()), 99.9)
    t_at_max = float(t[int(np.argmax(Q))])
    k1 = -np.log(1.0 - q_max / 100.0) / max(t_at_max, 1e-9)
    return [float(k1)], ([1e-6], [np.inf])


def _p0_bounds_higuchi(
    t: np.ndarray, Q: np.ndarray
) -> tuple[list[float], tuple[list[float], list[float]]]:
    kH = float(Q[-1]) / max(float(np.sqrt(t[-1])), 1e-9)
    return [kH], ([0.0], [np.inf])


def _p0_bounds_korsmeyer_peppas(
    t: np.ndarray, Q: np.ndarray
) -> tuple[list[float], tuple[list[float], list[float]]]:
    n_guess = 0.5
    pos = t > 0
    if pos.any():
        i = int(np.argmax(pos))
        k_guess = float(Q[i]) / max(float(np.power(t[i], n_guess)), 1e-9)
    else:
        k_guess = 1.0
    return [k_guess, n_guess], ([0.0, 1e-6], [np.inf, 2.0])


def _p0_bounds_weibull(
    t: np.ndarray, Q: np.ndarray
) -> tuple[list[float], tuple[list[float], list[float]]]:
    # beta ~ time at 63.2% dissolved (1/e inflection of Weibull)
    above = Q >= 63.2
    beta_guess = float(t[int(np.argmax(above))]) if above.any() else float(t[-1])
    beta_guess = max(beta_guess, 0.1)
    return [1.0, beta_guess], ([0.01, 0.01], [np.inf, np.inf])


# ──────────────────────────────────────────────────────────────────────────────
# Model registry  {name: (func, param_names, p0_bounds_fn)}
# ──────────────────────────────────────────────────────────────────────────────

_P0BoundsFn = Callable[
    [np.ndarray, np.ndarray],
    tuple[list[float], tuple[list[float], list[float]]],
]

_REGISTRY: dict[str, tuple[Callable[..., np.ndarray], list[str], _P0BoundsFn]] = {
    "zero_order": (_zero_order, ["k0"], _p0_bounds_zero_order),
    "first_order": (_first_order, ["k1"], _p0_bounds_first_order),
    "higuchi": (_higuchi, ["kH"], _p0_bounds_higuchi),
    "korsmeyer_peppas": (_korsmeyer_peppas, ["k", "n"], _p0_bounds_korsmeyer_peppas),
    "weibull": (_weibull, ["alpha", "beta"], _p0_bounds_weibull),
}

VALID_MODELS: frozenset[str] = frozenset(_REGISTRY.keys())

# ──────────────────────────────────────────────────────────────────────────────
# Dataclasses
# ──────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ModelFit:
    """Fit result for a single dissolution release model.

    Parameters
    ----------
    model_name : str
        Short model identifier (e.g. ``"weibull"``, ``"first_order"``).
    params : dict[str, float]
        Fitted parameter values keyed by name (empty dict if not converged).
    r_squared : float
        Coefficient of determination. Use for reference only; ranking uses AICc.
    aic : float
        Akaike Information Criterion (OLS reduced form).
    aicc : float
        AIC with small-sample correction. Use this for model ranking.
    bic : float
        Bayesian Information Criterion.
    n_points : int
        Number of data points used in the fit.
    n_params : int
        Number of fitted parameters.
    converged : bool
        True if ``scipy.optimize.curve_fit`` converged successfully.
    fitted_values : list[float]
        Model predictions at each observed time point (empty list if not converged).
    time_points : list[float]
        Time points at which the model was fitted.
    """

    model_name: str
    params: dict[str, float]
    r_squared: float
    aic: float
    aicc: float
    bic: float
    n_points: int
    n_params: int
    converged: bool
    fitted_values: list[float]
    time_points: list[float]

    def predict(self, t_new: np.ndarray) -> np.ndarray:
        """Evaluate the fitted model at new time points.

        Parameters
        ----------
        t_new : np.ndarray
            Time points at which to evaluate (minutes).

        Returns
        -------
        np.ndarray
            Predicted percent released at each time point.

        Raises
        ------
        RuntimeError
            If the model did not converge.
        """
        if not self.converged:
            raise RuntimeError(f"Model '{self.model_name}' did not converge; cannot predict.")
        func, param_names, _ = _REGISTRY[self.model_name]
        pvals = [self.params[k] for k in param_names]
        return func(np.asarray(t_new, dtype=float), *pvals)

    def to_dict(self) -> dict[str, object]:
        """Return a plain-dict representation of the fit result.

        Returns
        -------
        dict[str, object]
            All fit metrics serialized to basic Python types.
        """
        return {
            "model_name": self.model_name,
            "params": dict(self.params),
            "r_squared": self.r_squared,
            "aic": self.aic,
            "aicc": self.aicc,
            "bic": self.bic,
            "n_points": self.n_points,
            "n_params": self.n_params,
            "converged": self.converged,
        }


@dataclass
class DissolutionFitResults:
    """Results of dissolution model fitting for a single formulation.

    Parameters
    ----------
    formulation_label : str
        Label of the fitted formulation.
    time_points : list[float]
        Observed time points (minutes).
    observed_mean : list[float]
        Mean percent dissolved at each time point.
    fits : list[ModelFit]
        One ModelFit per requested model (converged and non-converged included).
    """

    formulation_label: str
    time_points: list[float]
    observed_mean: list[float]
    fits: list[ModelFit]

    @property
    def best(self) -> ModelFit:
        """Return the converged model with the lowest AICc.

        Returns
        -------
        ModelFit
            Best-ranking converged model.

        Raises
        ------
        ValueError
            If no models converged.
        """
        converged = [f for f in self.fits if f.converged]
        if not converged:
            raise ValueError("No models converged; cannot determine best model.")
        return min(converged, key=lambda m: m.aicc)

    def summary(self) -> str:
        """Return a human-readable text summary ranked by AICc.

        Returns
        -------
        str
            Multi-line summary table.
        """
        converged = sorted([f for f in self.fits if f.converged], key=lambda m: m.aicc)
        lines = [
            "Dissolution Model Fitting",
            "=========================",
            f"Formulation:  {self.formulation_label}",
            f"Timepoints:   {len(self.time_points)}  |  Fit target: mean profile",
            f"Models fitted: {len(self.fits)}  |  Converged: {len(converged)}",
            "",
        ]
        if not converged:
            lines.append("No models converged.")
            return "\n".join(lines)

        lines.append(f"{'Model':<22} {'R2':>6}  {'AICc':>8}  {'BIC':>8}  {'Params':<38}  Rank")
        lines.append("-" * 92)
        for rank, fit in enumerate(converged, 1):
            param_str = "  ".join(f"{k}={v:.4g}" for k, v in fit.params.items())
            tag = " [BEST]" if rank == 1 else ""
            lines.append(
                f"{fit.model_name:<22} {fit.r_squared:>6.4f}  {fit.aicc:>8.2f}"
                f"  {fit.bic:>8.2f}  {param_str:<38}  {rank}{tag}"
            )

        failed = [f for f in self.fits if not f.converged]
        if failed:
            lines += ["", f"Failed to converge: {', '.join(f.model_name for f in failed)}"]

        lines += [
            "",
            "Note: Ranked by AICc (lower is better). R2 shown for reference only.",
            "Fit characterises release mechanism; it is not a regulatory similarity",
            "test. Use f2 or bootstrap f2 for dissolution similarity assessment.",
        ]
        return "\n".join(lines)

    def plot(
        self,
        output_path: str | Path | None = None,
        show: bool = False,
    ) -> None:
        """Plot observed mean profile with fitted model curves overlaid.

        Parameters
        ----------
        output_path : str or Path or None, optional
            If provided, save the figure to this path (PNG/PDF/SVG).
        show : bool, optional
            If True, call ``plt.show()`` to display interactively. Default False.
        """
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        t_obs = np.array(self.time_points)
        Q_obs = np.array(self.observed_mean)
        t_dense = np.linspace(0.0, float(t_obs.max()), 300)

        colors = ["#e63946", "#457b9d", "#2a9d8f", "#e9c46a", "#f4a261"]
        linestyles = ["-", "--", "-.", ":", (0, (3, 1, 1, 1))]

        fig, ax = plt.subplots(figsize=(8, 5), dpi=600)
        ax.scatter(
            t_obs,
            Q_obs,
            color="#003366",
            s=55,
            zorder=5,
            label="Observed mean",
        )

        converged = sorted([f for f in self.fits if f.converged], key=lambda m: m.aicc)
        for i, fit in enumerate(converged):
            Q_fit = fit.predict(t_dense)
            label = f"{fit.model_name} (AICc={fit.aicc:.1f})"
            ax.plot(
                t_dense,
                Q_fit,
                color=colors[i % len(colors)],
                linestyle=linestyles[i % len(linestyles)],
                linewidth=1.8,
                label=label,
            )

        ax.set_xlabel("Time (min)", fontsize=11)
        ax.set_ylabel("Mean % Dissolved", fontsize=11)
        ax.set_title(
            f"Dissolution Model Fit  —  {self.formulation_label}",
            fontsize=12,
            fontweight="bold",
        )
        ax.set_ylim(0, 110)
        ax.legend(fontsize=9, loc="lower right")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()

        if output_path is not None:
            fig.savefig(output_path, bbox_inches="tight")
        if show:
            plt.show()
        plt.close(fig)

    def report(self, output_path: str | Path, format: str = "html") -> str | bytes:
        """Generate a model fit report.

        Parameters
        ----------
        output_path : str or Path
            Where to save the report.
        format : str, optional
            Output format: ``"html"``, ``"pdf"``, or ``"docx"``. Defaults to ``"html"``.

        Returns
        -------
        str | bytes
            Rendered content (str for html, bytes for pdf/docx).

        Raises
        ------
        ValueError
            If format is not a recognised format string.
        """
        if format not in {"html", "pdf", "docx"}:
            raise ValueError(f"format must be 'html', 'pdf', or 'docx', got {format!r}.")

        from openpkflow.dissolution.plotting import dissolution_fit_plot_b64

        t_dense = list(np.linspace(0.0, float(max(self.time_points)), 300))
        fit_curves = [
            (
                f.model_name,
                t_dense,
                f.predict(np.array(t_dense)).tolist(),
                f.aicc,
            )
            for f in self.fits
            if f.converged
        ]
        plot_b64 = dissolution_fit_plot_b64(
            time_points=self.time_points,
            observed_mean=self.observed_mean,
            fit_curves=fit_curves,
            formulation_label=self.formulation_label,
        )

        converged_sorted = sorted([f for f in self.fits if f.converged], key=lambda m: m.aicc)
        fit_rows: list[dict[str, object]] = []
        for rank, fit in enumerate(converged_sorted, 1):
            fit_rows.append(
                {
                    "model_name": fit.model_name,
                    "params": fit.params,
                    "r_squared": fit.r_squared,
                    "aic": fit.aic,
                    "aicc": fit.aicc,
                    "bic": fit.bic,
                    "n_points": fit.n_points,
                    "n_params": fit.n_params,
                    "converged": True,
                    "rank": rank,
                    "is_best": rank == 1,
                }
            )
        for fit in self.fits:
            if not fit.converged:
                fit_rows.append(
                    {
                        "model_name": fit.model_name,
                        "params": {},
                        "r_squared": float("nan"),
                        "aic": float("nan"),
                        "aicc": float("nan"),
                        "bic": float("nan"),
                        "n_points": fit.n_points,
                        "n_params": fit.n_params,
                        "converged": False,
                        "rank": None,
                        "is_best": False,
                    }
                )

        render_kwargs: dict[str, object] = dict(
            formulation_label=self.formulation_label,
            time_points=self.time_points,
            observed_mean=self.observed_mean,
            fit_rows=fit_rows,
            plot_b64=plot_b64,
            output_path=output_path,
        )

        if format == "html":
            from openpkflow.report.html import render_model_fit_html_report

            return render_model_fit_html_report(**render_kwargs)  # type: ignore[arg-type]

        if format == "pdf":
            from openpkflow.report.pdf import render_model_fit_pdf_report

            return render_model_fit_pdf_report(**render_kwargs)  # type: ignore[arg-type]

        from openpkflow.report.docx import render_model_fit_docx_report

        return render_model_fit_docx_report(**render_kwargs)  # type: ignore[arg-type]

    def to_dict(self) -> dict[str, object]:
        """Return a plain-dict representation of all fit results.

        Returns
        -------
        dict[str, object]
            Serialized fit results for all models.
        """
        return {
            "formulation_label": self.formulation_label,
            "time_points": self.time_points,
            "observed_mean": self.observed_mean,
            "fits": [f.to_dict() for f in self.fits],
        }


# ──────────────────────────────────────────────────────────────────────────────
# Internal fitter
# ──────────────────────────────────────────────────────────────────────────────


def _fit_single_model(
    name: str,
    func: Callable[..., np.ndarray],
    param_names: list[str],
    p0_bounds_fn: _P0BoundsFn,
    t: np.ndarray,
    Q: np.ndarray,
) -> ModelFit:
    """Fit one model to mean dissolution data. Returns ModelFit with converged=False on failure."""
    n = len(t)
    n_params = len(param_names)
    p0, bounds = p0_bounds_fn(t, Q)

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", OptimizeWarning)
            popt, _ = curve_fit(func, t, Q, p0=p0, bounds=bounds, maxfev=10_000)

        Q_pred = func(t, *popt)
        rss = float(np.sum((Q - Q_pred) ** 2))
        sst = float(np.sum((Q - Q.mean()) ** 2))
        r2 = 1.0 - rss / sst if sst > 1e-15 else 1.0

        # OLS-based information criteria (constants cancel across models, same n)
        rss_safe = max(rss, 1e-15)
        aic = n * float(np.log(rss_safe / n)) + 2.0 * n_params
        bic = n * float(np.log(rss_safe / n)) + n_params * float(np.log(n))
        denom = n - n_params - 1
        aicc = aic + 2.0 * n_params * (n_params + 1) / denom if denom > 0 else aic

        return ModelFit(
            model_name=name,
            params={pn: float(v) for pn, v in zip(param_names, popt, strict=True)},
            r_squared=float(r2),
            aic=float(aic),
            aicc=float(aicc),
            bic=float(bic),
            n_points=n,
            n_params=n_params,
            converged=True,
            fitted_values=Q_pred.tolist(),
            time_points=t.tolist(),
        )

    except (RuntimeError, ValueError):
        return ModelFit(
            model_name=name,
            params={},
            r_squared=float("nan"),
            aic=float("nan"),
            aicc=float("nan"),
            bic=float("nan"),
            n_points=n,
            n_params=n_params,
            converged=False,
            fitted_values=[],
            time_points=t.tolist(),
        )


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────


def fit_dissolution_models(
    time_points: list[float] | np.ndarray,
    observed_mean: list[float] | np.ndarray,
    formulation_label: str,
    models: list[str] | None = None,
) -> DissolutionFitResults:
    """Fit standard dissolution release models to a mean dissolution profile.

    Fits the mean profile (not per-vessel). Models are ranked by AICc.

    Parameters
    ----------
    time_points : list[float] or np.ndarray
        Time points in minutes (1-D, at least 3 points).
    observed_mean : list[float] or np.ndarray
        Mean percent dissolved at each time point (1-D, same length as time_points).
    formulation_label : str
        Label for the fitted formulation (used in reports and summaries).
    models : list[str] or None, optional
        Model names to fit. Defaults to all five:
        ``["zero_order", "first_order", "higuchi", "korsmeyer_peppas", "weibull"]``.
        Valid names: ``zero_order``, ``first_order``, ``higuchi``,
        ``korsmeyer_peppas``, ``weibull``.

    Returns
    -------
    DissolutionFitResults
        Fit results for all requested models. Use ``.best`` for the top-ranked
        model and ``.summary()`` for a ranked table.

    Raises
    ------
    ValueError
        If an unrecognised model name is given, fewer than 3 timepoints are
        supplied, or ``time_points`` and ``observed_mean`` differ in length.

    Notes
    -----
    - The Korsmeyer-Peppas power-law model is only valid up to ~60% release.
      A :class:`UserWarning` is raised when more than one timepoint exceeds 60%.
    - The Weibull model is empirical and FDA/EMA guidance notes it is not
      mechanistically interpretable for IVIVC. Use with caution.
    - Model fitting characterises release mechanism. It is **not** a regulatory
      similarity test; use f2 or bootstrap f2 for that purpose.
    """
    if models is None:
        models = list(_REGISTRY.keys())

    unknown = [m for m in models if m not in _REGISTRY]
    if unknown:
        raise ValueError(f"Unknown model(s): {unknown}. Valid models: {sorted(_REGISTRY.keys())}")

    t = np.asarray(time_points, dtype=float)
    Q = np.asarray(observed_mean, dtype=float)

    if t.ndim != 1 or Q.ndim != 1:
        raise ValueError("time_points and observed_mean must be 1-D arrays.")
    if len(t) != len(Q):
        raise ValueError(
            f"time_points and observed_mean must have the same length, got {len(t)} and {len(Q)}."
        )
    if len(t) < 3:
        raise ValueError("At least 3 timepoints are required for dissolution model fitting.")

    if "korsmeyer_peppas" in models:
        n_above_60 = int(np.sum(Q > 60.0))
        if n_above_60 > 1:
            warnings.warn(
                f"Korsmeyer-Peppas: {n_above_60} timepoints exceed 60% release. "
                "The power-law model is only mechanistically valid up to ~60% "
                "dissolved. Consider subsetting to early timepoints before fitting.",
                UserWarning,
                stacklevel=2,
            )

    fits = [_fit_single_model(name, *_REGISTRY[name], t, Q) for name in models]

    return DissolutionFitResults(
        formulation_label=formulation_label,
        time_points=t.tolist(),
        observed_mean=Q.tolist(),
        fits=fits,
    )


@dataclass(frozen=True)
class ModelComparisonResult:
    """Result of model-dependent dissolution profile comparison.

    FDA 1997 dissolution guidance recognises model-dependent approaches
    as alternatives to f2.  When a dissolution model fits both reference
    and test profiles, the similarity can be assessed by comparing fitted
    parameters via 90% confidence intervals.

    Parameters
    ----------
    model_name : str
        Name of the model used for comparison.
    param_name : str
        Parameter name being compared (e.g., ``"weibull_beta"``).
    ref_value : float
        Fitted parameter value for the reference profile.
    test_value : float
        Fitted parameter value for the test profile.
    se_diff : float
        Standard error of the difference (ref - test).
    ratio_pct : float
        Ratio of test to reference in percent (test / ref * 100).
    ci_lo : float
        Lower bound of the 90% confidence interval (percent scale).
    ci_hi : float
        Upper bound of the 90% confidence interval (percent scale).
    is_similar : bool
        True if the CI falls within a prescribed similarity window (default 80-125%).
    """

    model_name: str
    param_name: str
    ref_value: float
    test_value: float
    se_diff: float
    ratio_pct: float
    ci_lo: float
    ci_hi: float
    is_similar: bool

    def summary(self) -> str:
        """Return a textual summary of the model comparison.

        Returns
        -------
        str
            Single-line summary of parameter ratio and verdict.
        """
        verdict = "SIMILAR" if self.is_similar else "NOT SIMILAR"
        return (
            f"Model: {self.model_name}  Param: {self.param_name}  "
            f"Ratio: {self.ratio_pct:.1f}%  90% CI: "
            f"[{self.ci_lo:.1f}%, {self.ci_hi:.1f}%]  Verdict: {verdict}"
        )


def model_dependent_comparison(
    ref_time_points: list[float] | np.ndarray,
    ref_observed_mean: list[float] | np.ndarray,
    tst_time_points: list[float] | np.ndarray,
    tst_observed_mean: list[float] | np.ndarray,
    model: str,
    param_index: int = 0,
    *,
    ci_range: tuple[float, float] = (80.0, 125.0),
) -> ModelComparisonResult:
    """Compare fitted dissolution model parameters between two profiles via 90% CI.

    Fits the requested model to each profile independently, then tests
    whether the ratio of a selected fitted parameter falls within a
    similarity acceptance window (e.g., 80-125%).

    Parameters
    ----------
    ref_time_points : array-like
        Time points for the reference profile (minutes).
    ref_observed_mean : array-like
        Mean percent released for the reference profile.
    tst_time_points : array-like
        Time points for the test profile (minutes).
    tst_observed_mean : array-like
        Mean percent released for the test profile.
    model : str
        Model to fit (``"weibull"``, ``"first_order"``, etc.).
    param_index : int, optional
        Zero-based index of the parameter to compare (default 0).
    ci_range : tuple[float, float], optional
        Acceptance window in percent. Default (80, 125) per FDA standards.

    Returns
    -------
    ModelComparisonResult
        Comparison result with ratio, 90% CI bounds, and similarity verdict.

    Raises
    ------
    ValueError
        If the model is unknown, parameter index is out of range,
        or fewer than 3 timepoints are supplied.

    Notes
    -----
    Standard errors are estimated by propagating the per-profile fit standard
    errors (output of scipy.optimize.curve_fit).  The 90% CI uses a t(0.95, df)
    with df approximated by the combined sample degrees of freedom.

    This is an FDA-acknowledged alternative metric when f2 prerequisites
    (CV constraints, 85% rule) cannot be met.

    References
    ----------
    FDA Guidance for Industry: Dissolution Testing of Immediate Release Solid
    Oral Dosage Forms (1997). CDER. Section on model-dependent approaches.
    """
    import scipy.stats as st

    if model not in _REGISTRY:
        raise ValueError(f"Unknown model '{model}'. Valid models: {sorted(_REGISTRY.keys())}")

    t_ref = np.asarray(ref_time_points, dtype=float)
    Q_ref = np.asarray(ref_observed_mean, dtype=float)
    t_tst = np.asarray(tst_time_points, dtype=float)
    Q_tst = np.asarray(tst_observed_mean, dtype=float)

    if len(t_ref) < 3 or len(t_tst) < 3:
        raise ValueError("At least 3 timepoints required for each profile.")

    # Fit each profile
    ref_fit = _fit_single_model(model, *_REGISTRY[model], t_ref, Q_ref)
    tst_fit = _fit_single_model(model, *_REGISTRY[model], t_tst, Q_tst)

    if not ref_fit.converged:
        raise RuntimeError(f"Reference profile: model '{model}' did not converge.")
    if not tst_fit.converged:
        raise RuntimeError(f"Test profile: model '{model}' did not converge.")

    func_model, param_names, _p0_fn = _REGISTRY[model]
    n_ref = len(t_ref)
    n_tst = len(t_tst)

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", OptimizeWarning)
            popt_ref, pcov_ref = curve_fit(
                func_model,
                t_ref,
                Q_ref,
                maxfev=10_000,
            )
            popt_tst, pcov_tst = curve_fit(
                func_model,
                t_tst,
                Q_tst,
                maxfev=10_000,
            )
    except (RuntimeError, ValueError) as exc:
        raise RuntimeError(f"Failed to estimate parameter covariance: {exc}") from exc

    if param_index >= len(popt_ref):
        raise ValueError(
            f"Param index {param_index} out of range. "
            f"Available params ({len(popt_ref)}): {popt_ref.tolist()}"
        )

    ref_val = float(popt_ref[param_index])
    tst_val = float(popt_tst[param_index])
    param_name = param_names[param_index]

    # Standard errors
    se_ref = math.sqrt(max(pcov_ref[param_index, param_index], 1e-12))
    se_tst = math.sqrt(max(pcov_tst[param_index, param_index], 1e-12))
    se_diff = math.sqrt(se_ref**2 + se_tst**2)

    # 90% CI around ratio_pct using delta method: SE(ratio) = (1/ref) * se(tst - ref)
    ratio_pct = (tst_val / ref_val) * 100.0 if abs(ref_val) > 1e-12 else 100.0
    se_ratio_pct = (1.0 / abs(ref_val)) * se_diff * 100.0 if abs(ref_val) > 1e-12 else 0.0

    # degrees of freedom
    df = n_ref + n_tst - 2
    t_crit = float(st.t.ppf(0.95, df))

    ci_lo = ratio_pct - t_crit * se_ratio_pct
    ci_hi = ratio_pct + t_crit * se_ratio_pct
    is_similar = ci_lo >= ci_range[0] and ci_hi <= ci_range[1]

    return ModelComparisonResult(
        model_name=model,
        param_name=param_name,
        ref_value=ref_val,
        test_value=tst_val,
        se_diff=se_diff,
        ratio_pct=ratio_pct,
        ci_lo=ci_lo,
        ci_hi=ci_hi,
        is_similar=is_similar,
    )
