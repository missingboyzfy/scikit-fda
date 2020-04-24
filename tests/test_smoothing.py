import unittest

import skfda
from skfda._utils import _check_estimator
from skfda.representation.basis import BSpline, Monomial
from skfda.representation.grid import FDataGrid
import sklearn

import numpy as np
import skfda.preprocessing.smoothing as smoothing
import skfda.preprocessing.smoothing.kernel_smoothers as kernel_smoothers
import skfda.preprocessing.smoothing.validation as validation


class TestSklearnEstimators(unittest.TestCase):

    def test_nadaraya_watson(self):
        _check_estimator(kernel_smoothers.NadarayaWatsonSmoother)

    def test_local_linear_regression(self):
        _check_estimator(kernel_smoothers.LocalLinearRegressionSmoother)

    def test_knn(self):
        _check_estimator(kernel_smoothers.KNeighborsSmoother)


class _LinearSmootherLeaveOneOutScorerAlternative():
    r"""Alternative implementation of the LinearSmootherLeaveOneOutScorer"""

    def __call__(self, estimator, X, y):
        estimator_clone = sklearn.base.clone(estimator)

        estimator_clone._cv = True
        y_est = estimator_clone.fit_transform(X)

        return -np.mean((y.data_matrix[..., 0] - y_est.data_matrix[..., 0])**2)


class TestLeaveOneOut(unittest.TestCase):

    def _test_generic(self, estimator_class):
        loo_scorer = validation.LinearSmootherLeaveOneOutScorer()
        loo_scorer_alt = _LinearSmootherLeaveOneOutScorerAlternative()
        x = np.linspace(-2, 2, 5)
        fd = skfda.FDataGrid(x ** 2, x)

        estimator = estimator_class()

        grid = validation.SmoothingParameterSearch(
            estimator, [2, 3],
            scoring=loo_scorer)
        grid.fit(fd)
        score = np.array(grid.cv_results_['mean_test_score'])

        grid_alt = validation.SmoothingParameterSearch(
            estimator, [2, 3],
            scoring=loo_scorer_alt)
        grid_alt.fit(fd)
        score_alt = np.array(grid_alt.cv_results_['mean_test_score'])

        np.testing.assert_array_almost_equal(score, score_alt)

    def test_nadaraya_watson(self):
        self._test_generic(kernel_smoothers.NadarayaWatsonSmoother)

    def test_local_linear_regression(self):
        self._test_generic(kernel_smoothers.LocalLinearRegressionSmoother)

    def test_knn(self):
        self._test_generic(kernel_smoothers.KNeighborsSmoother)


class TestBasisSmoother(unittest.TestCase):

    def test_cholesky(self):
        t = np.linspace(0, 1, 5)
        x = np.sin(2 * np.pi * t) + np.cos(2 * np.pi * t)
        basis = BSpline((0, 1), n_basis=5)
        fd = FDataGrid(data_matrix=x, sample_points=t)
        smoother = smoothing.BasisSmoother(basis=basis,
                                           smoothing_parameter=10,
                                           regularization=2, method='cholesky',
                                           return_basis=True)
        fd_basis = smoother.fit_transform(fd)
        np.testing.assert_array_almost_equal(
            fd_basis.coefficients.round(2),
            np.array([[0.60, 0.47, 0.20, -0.07, -0.20]])
        )

    def test_qr(self):
        t = np.linspace(0, 1, 5)
        x = np.sin(2 * np.pi * t) + np.cos(2 * np.pi * t)
        basis = BSpline((0, 1), n_basis=5)
        fd = FDataGrid(data_matrix=x, sample_points=t)
        smoother = smoothing.BasisSmoother(basis=basis,
                                           smoothing_parameter=10,
                                           regularization=2, method='qr',
                                           return_basis=True)
        fd_basis = smoother.fit_transform(fd)
        np.testing.assert_array_almost_equal(
            fd_basis.coefficients.round(2),
            np.array([[0.60, 0.47, 0.20, -0.07, -0.20]])
        )

    def test_monomial_smoothing(self):
        # It does not have much sense to apply smoothing in this basic case
        # where the fit is very good but its just for testing purposes
        t = np.linspace(0, 1, 5)
        x = np.sin(2 * np.pi * t) + np.cos(2 * np.pi * t)
        basis = Monomial(n_basis=4)
        fd = FDataGrid(data_matrix=x, sample_points=t)
        smoother = smoothing.BasisSmoother(basis=basis,
                                           smoothing_parameter=1,
                                           regularization=2,
                                           return_basis=True)
        fd_basis = smoother.fit_transform(fd)
        # These results where extracted from the R package fda
        np.testing.assert_array_almost_equal(
            fd_basis.coefficients.round(2),
            np.array([[0.61, -0.88, 0.06, 0.02]]))
