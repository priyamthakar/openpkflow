"""Omega parameterization regression tests."""

from openpkflow.pop.estimation.omega import make_param_labels_omega


def test_full_omega_labels() -> None:
    assert make_param_labels_omega(["CL", "V", "KA"], "full") == [
        "log_cholesky_CL",
        "log_cholesky_V",
        "log_cholesky_KA",
        "cholesky_V_CL",
        "cholesky_KA_CL",
        "cholesky_KA_V",
    ]
