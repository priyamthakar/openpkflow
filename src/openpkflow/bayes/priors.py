"""Prior distributions for MAP individual PK estimation."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class PKPrior:
    """Log-normal priors on PK parameters for MAP individual estimation.

    Parameters
    ----------
    log_cl_mean : float
        Prior mean of log(CL) or log(CL_F). Default log(5.0) ~= 1.609.
    log_cl_sd : float
        Prior SD on log(CL). Default 1.0.
    log_v_mean : float
        Prior mean of log(Vz) or log(Vz_F). Default log(50.0) ~= 3.912.
    log_v_sd : float
        Prior SD on log(Vz). Default 1.0.
    log_ka_mean : float
        Prior mean of log(ka) for oral route. Default log(1.0) = 0.0.
    log_ka_sd : float
        Prior SD on log(ka). Default 1.0.
    sigma_mean : float
        Fixed proportional residual error (CV fraction). Default 0.2.
    log_cl_bounds : tuple[float, float]
        (lower, upper) log-space bounds for CL/CL_F. Default (-6, 6).
    log_v_bounds : tuple[float, float]
        (lower, upper) log-space bounds for Vz/Vz_F. Default (-2, 8).
    log_ka_bounds : tuple[float, float]
        (lower, upper) log-space bounds for ka. Default (-4, 4).
    """

    log_cl_mean: float = 1.609
    log_cl_sd: float = 1.0
    log_v_mean: float = 3.912
    log_v_sd: float = 1.0
    log_ka_mean: float = 0.0
    log_ka_sd: float = 1.0
    sigma_mean: float = 0.2
    log_cl_bounds: tuple[float, float] = (-6.0, 6.0)
    log_v_bounds: tuple[float, float] = (-2.0, 8.0)
    log_ka_bounds: tuple[float, float] = (-4.0, 4.0)

    def log_prior_oral(self, log_cl: float, log_v: float, log_ka: float) -> float:
        """Return log-prior density for oral route parameters.

        Parameters
        ----------
        log_cl : float
            log(CL_F).
        log_v : float
            log(Vz_F).
        log_ka : float
            log(ka).

        Returns
        -------
        float
            Sum of log-normal log-density values (<= 0).
        """
        return (
            _log_normal_logpdf(log_cl, self.log_cl_mean, self.log_cl_sd)
            + _log_normal_logpdf(log_v, self.log_v_mean, self.log_v_sd)
            + _log_normal_logpdf(log_ka, self.log_ka_mean, self.log_ka_sd)
        )

    def log_prior_iv(self, log_cl: float, log_v: float) -> float:
        """Return log-prior density for IV bolus route parameters.

        Parameters
        ----------
        log_cl : float
            log(CL).
        log_v : float
            log(Vz).

        Returns
        -------
        float
            Sum of log-normal log-density values (<= 0).
        """
        return (
            _log_normal_logpdf(log_cl, self.log_cl_mean, self.log_cl_sd)
            + _log_normal_logpdf(log_v, self.log_v_mean, self.log_v_sd)
        )


def _log_normal_logpdf(x: float, mean: float, sd: float) -> float:
    """Log-density of Normal(mean, sd) evaluated at x."""
    return -0.5 * ((x - mean) / sd) ** 2 - math.log(sd) - 0.5 * math.log(2 * math.pi)
