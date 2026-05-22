"""Full Bayesian individual PK estimation via PyMC (MCMC sampling).

Requires: pip install openpkflow[bayes]

This module provides full posterior inference over PK parameters using MCMC
(Metropolis-Hastings). For MAP point estimates without PyMC, use
:func:`openpkflow.bayes.map_individual_pk` instead.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import numpy as np


@dataclass
class BayesPKResult:
    """Full posterior result from Bayesian individual PK estimation.

    Attributes
    ----------
    subject : str
        Subject identifier.
    route : str
        Route of administration.
    dose : float
        Administered dose.
    n_observations : int
        Number of observed concentrations.
    n_samples : int
        Total MCMC posterior samples (chains x draws).
    cl_posterior : np.ndarray
        Posterior samples for CL (or CL_F for oral).
    v_posterior : np.ndarray
        Posterior samples for Vz (or Vz_F for oral).
    ka_posterior : np.ndarray or None
        Posterior samples for ka (oral only).
    cl_mean : float
        Posterior mean of CL or CL_F.
    v_mean : float
        Posterior mean of Vz or Vz_F.
    ka_mean : float or None
        Posterior mean of ka (oral only).
    cl_95ci : tuple[float, float]
        95% credible interval for CL or CL_F.
    v_95ci : tuple[float, float]
        95% credible interval for Vz or Vz_F.
    ka_95ci : tuple[float, float] or None
        95% credible interval for ka (oral only).
    half_life_mean : float
        Posterior mean half-life (h).
    AUCinf_mean : float
        Posterior mean AUCinf.
    shrinkage_cl : float
        Posterior shrinkage of CL towards prior (0 = no shrinkage, 1 = full).
    warnings : list[str]
        Diagnostic warnings.
    """

    subject: str
    route: str
    dose: float
    n_observations: int
    n_samples: int
    cl_posterior: np.ndarray
    v_posterior: np.ndarray
    ka_posterior: np.ndarray | None
    cl_mean: float
    v_mean: float
    ka_mean: float | None
    cl_95ci: tuple[float, float]
    v_95ci: tuple[float, float]
    ka_95ci: tuple[float, float] | None
    half_life_mean: float
    AUCinf_mean: float
    shrinkage_cl: float
    warnings: list[str] = field(default_factory=list)

    def summary(self) -> str:
        """Return a plain-text summary of the Bayesian PK result.

        Returns
        -------
        str
            ASCII summary with posterior means, 95% CIs, and disclaimer.
        """
        route_label = "oral (apparent)" if self.route == "oral" else "IV bolus"
        cl_name = "CL_F" if self.route == "oral" else "CL"
        v_name = "Vz_F" if self.route == "oral" else "Vz"
        title = f"Bayesian Individual PK{' -- ' + self.subject if self.subject else ''}"
        lines = [
            title,
            "=" * len(title),
            f"Route: {route_label} | Dose: {self.dose:.4g} | Obs: {self.n_observations}"
            f" | MCMC samples: {self.n_samples}",
            "",
            "Posterior Estimates (mean [95% CI]):",
            f"  {cl_name:5s} = {self.cl_mean:.4g}  [{self.cl_95ci[0]:.4g}, {self.cl_95ci[1]:.4g}] L/h",
            f"  {v_name:5s} = {self.v_mean:.4g}  [{self.v_95ci[0]:.4g}, {self.v_95ci[1]:.4g}] L",
        ]
        if self.route == "oral" and self.ka_mean is not None:
            lines.append(
                f"  {'ka':5s} = {self.ka_mean:.4g}  "
                f"[{self.ka_95ci[0]:.4g}, {self.ka_95ci[1]:.4g}] 1/h"  # type: ignore[index]
            )
        lines += [
            f"  t1/2  = {self.half_life_mean:.4g} h (posterior mean)",
            f"  AUCinf = {self.AUCinf_mean:.4g} h*conc (posterior mean)",
            f"  CL shrinkage towards prior = {self.shrinkage_cl:.1%}",
        ]
        if self.warnings:
            lines += ["", "Warnings:"] + [f"  [!] {w}" for w in self.warnings]
        lines += [
            "",
            "Disclaimer: This report was generated using OpenPKFlow (open-source).",
            "Final regulatory interpretation should be reviewed by qualified experts.",
        ]
        return "\n".join(lines)

    def to_dict(self) -> dict[str, object]:
        """Return a plain-dict representation (without raw posterior arrays).

        Returns
        -------
        dict[str, object]
            Summary statistics and metadata as basic Python types.
        """
        return {
            "subject": self.subject,
            "route": self.route,
            "dose": self.dose,
            "n_observations": self.n_observations,
            "n_samples": self.n_samples,
            "cl_mean": self.cl_mean,
            "v_mean": self.v_mean,
            "ka_mean": self.ka_mean,
            "cl_95ci": self.cl_95ci,
            "v_95ci": self.v_95ci,
            "ka_95ci": self.ka_95ci,
            "half_life_mean": self.half_life_mean,
            "AUCinf_mean": self.AUCinf_mean,
            "shrinkage_cl": self.shrinkage_cl,
            "warnings": self.warnings,
        }


def bayes_individual_pk(
    times: list[float] | np.ndarray,
    concentrations: list[float] | np.ndarray,
    dose: float,
    route: Literal["oral", "iv_bolus"],
    prior: object | None = None,
    *,
    n_samples: int = 1000,
    tune: int = 1000,
    chains: int = 2,
    subject: str = "",
) -> BayesPKResult:
    """Estimate individual PK parameters via full Bayesian MCMC sampling.

    Uses PyMC with Metropolis-Hastings sampling (NUTS cannot be used because the
    PK model is a blackbox numpy function without PyTensor gradients). For faster
    MAP point estimates, use :func:`openpkflow.bayes.map_individual_pk` instead.

    Parameters
    ----------
    times : array-like
        Sampling times in hours. Minimum: oral >= 3, iv_bolus >= 2.
    concentrations : array-like
        Observed concentrations.
    dose : float
        Administered dose.
    route : {"oral", "iv_bolus"}
        Route of administration.
    prior : PKPrior or None, optional
        Log-normal priors. Uses defaults if None.
    n_samples : int, optional
        MCMC draws per chain after tuning. Default 1000.
    tune : int, optional
        MCMC tuning steps per chain. Default 1000.
    chains : int, optional
        Number of independent chains. Default 2.
    subject : str, optional
        Subject identifier for labelling.

    Returns
    -------
    BayesPKResult
        Full posterior samples and summary statistics.

    Raises
    ------
    ImportError
        If PyMC is not installed (pip install openpkflow[bayes]).
    ValueError
        If route is unsupported or minimum observations not met.

    References
    ----------
    Sheiner LB & Beal SL (1982) Bayesian individualization of PK.
    J Pharm Sci 71:1344-8. DOI:10.1002/jps.2600710906
    """
    try:
        import pymc as pm
        import pytensor.tensor as pt
        from pytensor.compile.ops import as_op
    except ImportError as exc:
        raise ImportError(
            "Full Bayesian PK requires PyMC. Install with: pip install openpkflow[bayes]"
        ) from exc

    from openpkflow.bayes.priors import PKPrior
    from openpkflow.sim.methods import c_1cmt_iv_bolus, c_1cmt_oral

    _MIN_OBS = {"oral": 3, "iv_bolus": 2}
    if route not in _MIN_OBS:
        raise ValueError(f"Unsupported route '{route}'. Choose 'oral' or 'iv_bolus'.")
    if dose <= 0:
        raise ValueError("dose must be > 0.")
    prior = prior or PKPrior()

    t = np.asarray(times, dtype=float)
    c = np.asarray(concentrations, dtype=float)
    if len(t) < _MIN_OBS[route]:
        raise ValueError(
            f"Route '{route}' requires >= {_MIN_OBS[route]} observations; got {len(t)}."
        )

    sigma_fixed = prior.sigma_mean

    # Wrap PK log-likelihood as a PyTensor blackbox op (no gradient -> Metropolis)
    if route == "oral":
        @as_op(itypes=[pt.dscalar, pt.dscalar, pt.dscalar], otypes=[pt.dscalar])
        def _pk_ll(log_cl, log_v, log_ka):
            try:
                c_pred = c_1cmt_oral(t, dose, float(np.exp(log_cl)),
                                     float(np.exp(log_v)), float(np.exp(log_ka)))
                ll = 0.0
                for obs, pred in zip(c, c_pred):
                    sd = sigma_fixed * abs(float(pred)) + 1e-9
                    ll += -0.5 * ((float(obs) - float(pred)) / sd) ** 2 - math.log(sd)
                return np.float64(ll)
            except Exception:
                return np.float64(-1e12)
    else:
        @as_op(itypes=[pt.dscalar, pt.dscalar], otypes=[pt.dscalar])
        def _pk_ll(log_cl, log_v):
            try:
                c_pred = c_1cmt_iv_bolus(t, dose, float(np.exp(log_cl)), float(np.exp(log_v)))
                ll = 0.0
                for obs, pred in zip(c, c_pred):
                    sd = sigma_fixed * abs(float(pred)) + 1e-9
                    ll += -0.5 * ((float(obs) - float(pred)) / sd) ** 2 - math.log(sd)
                return np.float64(ll)
            except Exception:
                return np.float64(-1e12)

    warn_list: list[str] = []

    with pm.Model():
        log_cl = pm.Normal("log_cl", mu=prior.log_cl_mean, sigma=prior.log_cl_sd)
        log_v = pm.Normal("log_v", mu=prior.log_v_mean, sigma=prior.log_v_sd)

        if route == "oral":
            log_ka = pm.Normal("log_ka", mu=prior.log_ka_mean, sigma=prior.log_ka_sd)
            pm.Potential("pk_ll", _pk_ll(log_cl, log_v, log_ka))
        else:
            log_ka = None
            pm.Potential("pk_ll", _pk_ll(log_cl, log_v))

        import warnings as _w
        with _w.catch_warnings():
            _w.simplefilter("ignore")
            trace = pm.sample(
                n_samples,
                tune=tune,
                chains=chains,
                step=pm.Metropolis(),
                progressbar=False,
                return_inferencedata=True,
            )

    # Extract posterior samples (flatten chains)
    post = trace.posterior
    cl_samples = np.exp(post["log_cl"].values.flatten()).astype(float)
    v_samples = np.exp(post["log_v"].values.flatten()).astype(float)
    ka_samples = (
        np.exp(post["log_ka"].values.flatten()).astype(float)
        if route == "oral"
        else None
    )

    def _ci95(arr: np.ndarray) -> tuple[float, float]:
        return (float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5)))

    cl_mean = float(np.mean(cl_samples))
    v_mean = float(np.mean(v_samples))
    ka_mean = float(np.mean(ka_samples)) if ka_samples is not None else None

    # Posterior half-life and AUCinf from samples
    k_samples = cl_samples / v_samples
    t12_samples = np.log(2.0) / k_samples
    aucinf_samples = dose / cl_samples

    # Shrinkage: (prior SD - posterior SD) / prior SD
    cl_prior_sd_nat = math.exp(prior.log_cl_mean) * (math.exp(prior.log_cl_sd) - 1.0)
    cl_post_sd_nat = float(np.std(cl_samples, ddof=1))
    shrinkage = max(0.0, (cl_prior_sd_nat - cl_post_sd_nat) / (cl_prior_sd_nat + 1e-9))

    # Check effective sample size
    try:
        import arviz as az
        ess = az.ess(trace)
        min_ess = float(min(ess["log_cl"].values.min(), ess["log_v"].values.min()))
        if min_ess < 100 * chains:
            warn_list.append(
                f"Low effective sample size (min ESS = {min_ess:.0f}). "
                "Consider increasing n_samples or tune."
            )
    except Exception:
        pass

    return BayesPKResult(
        subject=subject,
        route=route,
        dose=dose,
        n_observations=len(t),
        n_samples=len(cl_samples),
        cl_posterior=cl_samples,
        v_posterior=v_samples,
        ka_posterior=ka_samples,
        cl_mean=cl_mean,
        v_mean=v_mean,
        ka_mean=ka_mean,
        cl_95ci=_ci95(cl_samples),
        v_95ci=_ci95(v_samples),
        ka_95ci=_ci95(ka_samples) if ka_samples is not None else None,
        half_life_mean=float(np.mean(t12_samples)),
        AUCinf_mean=float(np.mean(aucinf_samples)),
        shrinkage_cl=shrinkage,
        warnings=warn_list,
    )
