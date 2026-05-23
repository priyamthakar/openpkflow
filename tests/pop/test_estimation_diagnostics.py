"""Tests for estimation diagnostics."""

import numpy as np

from openpkflow.pop.estimation.diagnostics import (
    check_at_bounds,
    check_gradient_norm,
    check_hessian,
    compute_ebd_shrinkage,
    numerical_hessian,
)


class TestNumericalHessian:
    def test_quadratic(self) -> None:
        def f(x):
            return 2 * x[0] ** 2 + 3 * x[1] ** 2

        x = np.array([0.0, 0.0])
        H = numerical_hessian(f, x, eps=1e-4)
        np.testing.assert_allclose(np.diag(H), [4.0, 6.0], rtol=0.01)

    def test_symmetry(self) -> None:
        def f(x):
            return x[0] ** 2 * x[1] + x[1] ** 3

        x = np.array([1.0, 2.0])
        H = numerical_hessian(f, x)
        assert np.allclose(H, H.T)


class TestCheckHessian:
    def test_positive_definite(self) -> None:
        H = np.array([[4.0, 0.1], [0.1, 3.0]])
        warn_list: list[str] = []
        ok, cond, inv = check_hessian(H, warn_list)
        assert ok is True
        assert inv is not None
        assert not warn_list

    def test_not_positive_definite(self) -> None:
        H = np.array([[-1.0, 0.0], [0.0, -2.0]])
        warn_list: list[str] = []
        ok, cond, inv = check_hessian(H, warn_list)
        assert ok is False
        assert inv is None
        assert any("not positive-definite" in w for w in warn_list)

    def test_high_condition_number_warns(self) -> None:
        H = np.array([[1e8, 0.0], [0.0, 1e-8]])
        warn_list: list[str] = []
        ok, cond, inv = check_hessian(H, warn_list)
        assert ok is True
        assert inv is not None
        assert any("condition number" in w.lower() for w in warn_list)


class TestCheckAtBounds:
    def test_at_lower_bound(self) -> None:
        x = np.array([-5.999])
        bounds: list[tuple[float, float]] = [(-6.0, 6.0)]
        warn_list: list[str] = []
        check_at_bounds(x, bounds, ["param1"], warn_list)
        assert any("lower bound" in w.lower() for w in warn_list)

    def test_not_at_bound(self) -> None:
        x = np.array([0.0])
        bounds: list[tuple[float, float]] = [(-6.0, 6.0)]
        warn_list: list[str] = []
        check_at_bounds(x, bounds, ["param1"], warn_list)
        assert len(warn_list) == 0


class TestCheckGradientNorm:
    def test_small_gradient(self) -> None:
        def f(x):
            return 100.0 * (x[0] - 0.5) ** 2

        x = np.array([0.5])
        warn_list: list[str] = []
        gnorm = check_gradient_norm(x, f, warn_list)
        assert gnorm < 0.1
        assert len(warn_list) == 0

    def test_large_gradient_warns(self) -> None:
        def f(x):
            return x[0] ** 2

        x = np.array([1.0])
        warn_list: list[str] = []
        gnorm = check_gradient_norm(x, f, warn_list)
        assert gnorm > 0.1
        assert len(warn_list) > 0


class TestComputeEBEShrinkage:
    def test_full_shrinkage(self) -> None:
        ebe = np.array([[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]])
        omega = {"CL": 0.1, "Vz": 0.1}
        shrinkage = compute_ebd_shrinkage(ebe, omega, ["CL", "Vz"])
        assert abs(shrinkage["CL"] - 1.0) < 0.01

    def test_no_shrinkage(self) -> None:
        ebe = np.random.default_rng(42).normal(0, 0.3, (100, 2))
        omega = {"CL": 0.1, "Vz": 0.1}
        shrinkage = compute_ebd_shrinkage(ebe, omega, ["CL", "Vz"])
        assert shrinkage["CL"] < 0.5

    def test_single_subject(self) -> None:
        ebe = np.array([[0.1, -0.2]])
        omega = {"CL": 0.1, "Vz": 0.1}
        shrinkage = compute_ebd_shrinkage(ebe, omega, ["CL", "Vz"])
        assert shrinkage["CL"] == 1.0
        assert shrinkage["Vz"] == 1.0
