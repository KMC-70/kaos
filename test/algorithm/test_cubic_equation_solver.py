"""Test for cubic equation solver."""

from unittest import TestCase
from numpy.testing import assert_array_almost_equal
from ddt import ddt, data

from kaos.algorithm.cubic_equation_solver import solve

@ddt
class KaosTestCase(TestCase):
    """Tests cubic equation solver's accuracy"""
    @data(((0,0,1,1),[-1]),              # linear
          ((0,1,0,-1),[1,-1]),           # quadratic
          ((1,0,0,0),[0]),               # cubic repeated roots
          ((2,-4,-22, 24),[4, -3, 1]),   # cubic 3 roots
          ((-4,-41,-221,1),[0.004521]))  # cubic 1 real 2 imaginary roots
    def test_cubic_equation_solver_accuracy(self,data):
        """Test data format: Tuple of coefficients, list of answers"""
        coefficients, expected_result = data
        assert_array_almost_equal(solve(*coefficients), expected_result)

