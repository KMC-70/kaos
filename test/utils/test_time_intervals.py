"""Testing KAOS's interval utility functions."""

from ddt import ddt, unpack, data

from numpy.testing import assert_array_equal
from mpmath import mpf

from kaos.utils.time_intervals import fuse_neighbor_intervals, trim_poi_segments
from kaos.tuples import TimeInterval
from .. import KaosTestCase


@ddt
class TestIntervalUtilis(KaosTestCase):
    """Tests time conversions utilities."""

    @unpack
    @data(
        ([], []),
        ([(1, 2), (2, 3)], [(1, 3)]),
        ([(1, 2), (2, 3), (40, 50), (12, 15), (15, 16)], [(1, 3), (12, 16), (40, 50)]),
        ([(mpf("1.01"), mpf("1.02")), (mpf("1.02"), mpf("1.03"))], [(mpf("1.01"), mpf("1.03"))])
    )
    def test_fuse_neighbor_intervals(self, input_interval_list, expected):
        """Tests fuse_neighbor_intervals, see function docstring for assumptions/limitations"""
        time_interval_list = [TimeInterval(*interval) for interval in input_interval_list]
        result = fuse_neighbor_intervals(time_interval_list)
        assert_array_equal(result, expected)

    @unpack
    @data(
        ([], (1, 2), []),
        ([(5, 20), (25, 60), (70, 90)], (0, 10), [(5, 10)]),
        ([(5, 20), (25, 60), (70, 90)], (76, 100), [(76, 90)]),
        ([(5, 20), (25, 60), (70, 90)], (10, 50), [(10, 20), (25, 50)]),
        ([(5, 20), (25, 60), (70, 90)], (1, 30), [(5, 20), (25, 30)]),
        ([(5, 20), (25, 60), (70, 90)], (70, 90), [(70, 90)]),
        ([(1552501000, 1552501500), (1552506000, 1552510000)], (1552501400, 1552507000),
            [(1552501400, 1552501500), (1552506000, 1552507000)]),
        ([(1552501000, 1552501500), (1552506000, 1552510000)], (1552501400, 1552507000),
            [(1552501400, 1552501500), (1552506000, 1552507000)]),
    )
    def test_trim_poi_segments(self, input_interval_list, poi, expected):
        """Tests that the UTC to UNIX time converter detects format and date errors."""
        time_interval_list = [TimeInterval(*interval) for interval in input_interval_list]
        poi = TimeInterval(*poi)
        result = trim_poi_segments(time_interval_list, poi)
        assert_array_equal(result, expected)
