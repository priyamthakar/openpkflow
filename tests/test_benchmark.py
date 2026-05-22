"""Performance benchmarks for core pharmacokinetic / dissolution functions."""

from __future__ import annotations

import numpy as np
import pytest

from openpkflow.be.methods import be_tost
from openpkflow.dissolution.similarity import f2
from openpkflow.dissolution.models import fit_dissolution_models
from openpkflow.nca.methods import auc_linear


@pytest.mark.benchmark(group="dissolution")
def test_f2_benchmark(benchmark):
    """Benchmark f2 on a typical 5-timepoint dissolution profile."""
    ref = [20.0, 40.0, 60.0, 80.0, 90.0]
    tst = [21.0, 39.0, 61.0, 79.0, 88.0]
    result = benchmark(f2, ref, tst)
    assert result > 50.0


@pytest.mark.benchmark(group="dissolution")
def test_fit_models_benchmark(benchmark):
    """Benchmark dissolution model fitting on 12-timepoint profiles."""
    np.random.seed(42)
    t = np.linspace(5, 120, 12)
    Q = 100 * (1 - np.exp(-0.03 * t)) + np.random.normal(0, 1, len(t))
    Q = np.clip(Q, 0, 100)
    benchmark(fit_dissolution_models, t.tolist(), Q.tolist(), "bench")


@pytest.mark.benchmark(group="nca")
def test_auc_trapezoid_benchmark(benchmark):
    """Benchmark trapezoidal AUC on 20-point concentration-time series."""
    t = np.concatenate([
        np.linspace(0, 2, 8),
        np.linspace(2.5, 24, 12),
    ])
    conc = np.exp(-0.3 * t) * 50
    conc[0] = 0
    benchmark(auc_linear, t.tolist(), conc.tolist())


@pytest.mark.benchmark(group="be")
def test_tost_benchmark(benchmark):
    """Benchmark 2x2 crossover TOST on 24-subject dataset."""
    np.random.seed(42)
    n = 24
    mu_r = np.log(100)
    mu_t = np.log(95)
    sigma_w = 0.2
    log_ref = np.random.normal(mu_r, sigma_w, n)
    log_test = np.random.normal(mu_t, sigma_w, n)
    benchmark(be_tost, log_ref, log_test, alpha=0.05, be_lower=0.80, be_upper=1.25)
