"""Performance benchmarks for core pharmacokinetic / dissolution functions.

Run with:
    pytest tests/test_benchmark.py --benchmark-only
    pytest tests/test_benchmark.py --benchmark-only --benchmark-sort=mean
    pytest tests/test_benchmark.py --benchmark-only --benchmark-compare
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from openpkflow.bayes import map_individual_pk
from openpkflow.be.methods import be_tost
from openpkflow.dissolution import bootstrap_f2
from openpkflow.dissolution.models import fit_dissolution_models
from openpkflow.dissolution.similarity import f1, f2
from openpkflow.ivivc.methods import convolution_predict, wagner_nelson
from openpkflow.nca.methods import auc_linear, auc_linear_up_log_down, lambda_z
from openpkflow.nca.sparse import fit_sparse_1cmt_oral
from openpkflow.sim.dosing import DoseRegimen
from openpkflow.sim.methods import c_1cmt_iv_bolus, c_1cmt_oral, c_2cmt_iv_bolus
from openpkflow.sim.models import OneCompartmentModel, TwoCompartmentModel
from openpkflow.sim.simulate import simulate

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_TIMES_DENSE = np.linspace(0, 72, 500)
_IV_T = np.linspace(0.5, 24, 20)
_IV_C = 3.0 * np.exp(-0.15 * _IV_T)
_MAP_TIMES = [0.5, 1.0, 2.0, 4.0, 8.0, 12.0]
_MAP_CONCS = [1.23, 1.85, 1.97, 1.61, 0.89, 0.49]
_SPARSE_T = [0.5, 2.0, 8.0, 24.0]
_SPARSE_C = [1.2, 2.3, 1.5, 0.4]
_DOSE = 100.0

# ---------------------------------------------------------------------------
# Dissolution
# ---------------------------------------------------------------------------


@pytest.mark.benchmark(group="dissolution")
def test_f2_benchmark(benchmark):
    """f2 on a 5-timepoint dissolution profile."""
    ref = [20.0, 40.0, 60.0, 80.0, 90.0]
    tst = [21.0, 39.0, 61.0, 79.0, 88.0]
    result = benchmark(f2, ref, tst)
    assert result > 50.0


@pytest.mark.benchmark(group="dissolution")
def test_f1_benchmark(benchmark):
    """f1 on a 5-timepoint dissolution profile."""
    ref = [20.0, 40.0, 60.0, 80.0, 90.0]
    tst = [21.0, 39.0, 61.0, 79.0, 88.0]
    result = benchmark(f1, ref, tst)
    assert result >= 0.0


@pytest.mark.benchmark(group="dissolution")
def test_bootstrap_f2_benchmark(benchmark):
    """bootstrap_f2 with 500 replicates on a 5-timepoint profile (6 vessels each)."""
    rng = np.random.default_rng(42)
    # bootstrap_f2 expects 2-D arrays: (n_vessels, n_timepoints)
    ref = np.tile([20.0, 40.0, 60.0, 80.0, 90.0], (6, 1)) + rng.normal(0, 1.5, (6, 5))
    tst = np.tile([21.0, 39.0, 61.0, 79.0, 88.0], (6, 1)) + rng.normal(0, 1.5, (6, 5))
    result = benchmark(bootstrap_f2, ref, tst, n_replicates=500, seed=42)
    assert result.f2_observed > 0


@pytest.mark.benchmark(group="dissolution")
def test_fit_models_benchmark(benchmark):
    """Dissolution model fitting (5 models) on 12-timepoint profile."""
    rng = np.random.default_rng(42)
    t = np.linspace(5, 120, 12)
    Q = 100 * (1 - np.exp(-0.03 * t)) + rng.normal(0, 1, len(t))
    Q = np.clip(Q, 0, 100)
    benchmark(fit_dissolution_models, t.tolist(), Q.tolist(), "bench")


# ---------------------------------------------------------------------------
# NCA
# ---------------------------------------------------------------------------


@pytest.mark.benchmark(group="nca")
def test_auc_linear_benchmark(benchmark):
    """Linear trapezoidal AUC on 20-point concentration-time series."""
    t = np.concatenate([np.linspace(0, 2, 8), np.linspace(2.5, 24, 12)])
    conc = np.exp(-0.3 * t) * 50
    conc[0] = 0.0
    benchmark(auc_linear, t.tolist(), conc.tolist())


@pytest.mark.benchmark(group="nca")
def test_auc_linear_up_log_down_benchmark(benchmark):
    """Linear-up-log-down AUC on 20-point series with biexponential decline."""
    t = np.linspace(0.25, 24, 20)
    conc = 10 * np.exp(-0.3 * t) + 5 * np.exp(-0.05 * t)
    benchmark(auc_linear_up_log_down, t.tolist(), conc.tolist())


@pytest.mark.benchmark(group="nca")
def test_lambda_z_benchmark(benchmark):
    """lambda_z auto-selection on 10-point log-linear terminal phase."""
    t = np.array([4.0, 6.0, 8.0, 12.0, 16.0, 20.0, 24.0, 32.0, 40.0, 48.0])
    conc = 8.0 * np.exp(-0.12 * t)
    benchmark(lambda_z, t.tolist(), conc.tolist())


@pytest.mark.benchmark(group="nca")
def test_sparse_nca_benchmark(benchmark):
    """fit_sparse_1cmt_oral on a 4-sample minimal dataset."""
    result = benchmark(fit_sparse_1cmt_oral, _SPARSE_T, _SPARSE_C, _DOSE)
    assert result.AUCinf > 0


# ---------------------------------------------------------------------------
# PK simulation
# ---------------------------------------------------------------------------


@pytest.mark.benchmark(group="sim")
def test_c_1cmt_oral_benchmark(benchmark):
    """Analytical 1-cmt oral concentration at 500 time points."""
    benchmark(c_1cmt_oral, _TIMES_DENSE, 100.0, 5.0, 50.0, 1.2)


@pytest.mark.benchmark(group="sim")
def test_c_1cmt_iv_bolus_benchmark(benchmark):
    """Analytical 1-cmt IV bolus concentration at 500 time points."""
    benchmark(c_1cmt_iv_bolus, _TIMES_DENSE, 100.0, 5.0, 50.0)


@pytest.mark.benchmark(group="sim")
def test_c_2cmt_iv_bolus_benchmark(benchmark):
    """Analytical 2-cmt IV bolus concentration at 500 time points."""
    benchmark(c_2cmt_iv_bolus, _TIMES_DENSE, 100.0, 3.0, 20.0, 5.0, 30.0)


@pytest.mark.benchmark(group="sim")
def test_simulate_1cmt_oral_repeated_benchmark(benchmark):
    """simulate() with 1-cmt oral model, 5 doses, 500 time points."""
    model = OneCompartmentModel(route="oral", CL_F=5.0, Vz_F=50.0, ka=1.2)
    regimen = DoseRegimen.from_repeated(amount=100.0, route="oral", tau=24.0, n_doses=5)
    benchmark(simulate, model, regimen, _TIMES_DENSE)


@pytest.mark.benchmark(group="sim")
def test_simulate_2cmt_iv_repeated_benchmark(benchmark):
    """simulate() with 2-cmt IV model, 3 doses, 500 time points."""
    model = TwoCompartmentModel(route="iv_bolus", CL=3.0, V1=20.0, Q=5.0, V2=30.0)
    regimen = DoseRegimen.from_repeated(amount=100.0, route="iv_bolus", tau=24.0, n_doses=3)
    benchmark(simulate, model, regimen, _TIMES_DENSE)


# ---------------------------------------------------------------------------
# IVIVC
# ---------------------------------------------------------------------------

_ORAL_T = np.array([0.5, 1.0, 2.0, 4.0, 6.0, 8.0, 12.0, 16.0, 24.0])
_ORAL_C = np.array([0.8, 1.5, 2.1, 2.4, 2.0, 1.6, 1.0, 0.6, 0.25])


@pytest.mark.benchmark(group="ivivc")
def test_wagner_nelson_benchmark(benchmark):
    """Wagner-Nelson deconvolution on 9-point oral profile."""
    benchmark(wagner_nelson, _ORAL_T.tolist(), _ORAL_C.tolist(), kel=0.15)


@pytest.mark.benchmark(group="ivivc")
def test_convolution_predict_benchmark(benchmark):
    """Convolution prediction with 50-point dissolution input and IV impulse response."""
    fa_times = np.linspace(0, 24, 50)
    fa_values = 1 - np.exp(-0.3 * fa_times)
    benchmark(
        convolution_predict,
        fa_times.tolist(),
        fa_values.tolist(),
        iv_unit_impulse_times=_IV_T.tolist(),
        iv_unit_impulse_concs=_IV_C.tolist(),
    )


# ---------------------------------------------------------------------------
# MAP Bayesian PK
# ---------------------------------------------------------------------------


@pytest.mark.benchmark(group="bayes")
def test_map_pk_oral_benchmark(benchmark):
    """MAP individual PK estimation on a 6-point oral profile."""
    result = benchmark(map_individual_pk, _MAP_TIMES, _MAP_CONCS, 100.0, "oral")
    assert result.converged


@pytest.mark.benchmark(group="bayes")
def test_map_pk_iv_benchmark(benchmark):
    """MAP individual PK estimation on a 4-point IV bolus profile."""
    t = [0.25, 1.0, 3.0, 8.0]
    c = [3.8, 2.9, 1.8, 0.7]
    result = benchmark(map_individual_pk, t, c, 100.0, "iv_bolus")
    assert result.converged


# ---------------------------------------------------------------------------
# Bioequivalence
# ---------------------------------------------------------------------------


@pytest.mark.benchmark(group="be")
def test_tost_benchmark(benchmark):
    """2x2 crossover TOST on 24-subject dataset."""
    rng = np.random.default_rng(42)
    n = 24
    log_ref = rng.normal(math.log(100), 0.2, n)
    log_test = rng.normal(math.log(95), 0.2, n)
    benchmark(be_tost, log_ref, log_test, alpha=0.05, be_lower=0.80, be_upper=1.25)
