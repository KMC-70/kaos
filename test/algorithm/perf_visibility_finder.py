"""Visibility Finder Test File."""

from __future__ import print_function
import mpmath as mp
import numpy as np

from ddt import ddt, data

from kaos.algorithm.visibility_finder import VisibilityFinder
from kaos.algorithm import view_cone
from kaos.tuples import TimeInterval
from kaos.models import Satellite
from kaos.models.parser import parse_ephemeris_file

from .. import KaosTestCase

@ddt
class TestVisibilityFinderPerf(KaosTestCase):
    """Test the visibility finder's accuracy."""

    @classmethod
    def setUpClass(cls):
        super(TestVisibilityFinderPerf, cls).setUpClass()
        parse_ephemeris_file("ephemeris/Radarsat2.e")

    @data(('test/test_data/vancouver.test', (1514764800, 1514764800 + 5 * 24 * 60 * 60)))
    def test_visibility_perf(self, test_data):
        """Tests that the visibility finder produces the same results as the access file and prints
        accuracy and performance measurements at the end.
        This test is meant to be run manually (not as part of the automated CI tests).

        Use: pytest -s test/algorithm/perf_visibiliry_finder.py

        Args:
            test_data (tuple): A three tuple containing the:
                                1 - The path of KAOS access test file
                                2 - A tuple of the desired test duration
        """
        access_file, interval = test_data

        access_info = self.parse_access_file(access_file)
        finder = VisibilityFinder(Satellite.get_by_name(access_info.sat_name)[0].platform_id,
                                  access_info.target, interval)

        # NOTE: change to burte_force=True to switch to brute-force method.
        access_times = np.asarray(finder.profile_determine_visibility(brute_force=False))

        interval = TimeInterval(*interval)
        expected_accesses = view_cone._trim_poi_segments(access_info.accesses, interval)

        fail = False
        total_error = 0
        print("=============================== visibility report ===============================")
        for exp_start, exp_end in expected_accesses:
            idx = (np.abs(np.transpose(access_times)[0] - exp_start)).argmin()
            error = abs(exp_start - access_times[idx][0]) + abs(exp_end - access_times[idx][1])
            if error > 600:
                fail = True
                print("start, {}, ------------, {}"
                    .format(exp_start, mp.nstr(access_times[idx][0] - exp_start, 6)))
                print("end,   {}, ------------, {}"
                    .format(exp_end, mp.nstr(access_times[idx][1] - exp_end, 6)))
            else:
                print("start, {}, {}, {}"
                    .format(exp_start, mp.nstr(access_times[idx][0], 11),
                        mp.nstr(access_times[idx][0] - exp_start, 6)))
                print("end  , {}, {}, {}"
                    .format(exp_end, mp.nstr(access_times[idx][1], 11),
                        mp.nstr(access_times[idx][1] - exp_end, 6)))
                total_error += error
                access_times = np.delete(access_times, idx, axis=0)

        print("\nTotal Error: {}".format(mp.nstr(total_error, 12)))
        print("Average Error: {}".format(mp.nstr(total_error / (len(expected_accesses) * 2))))
        if fail:
            raise Exception("Missing accesses. Unmatched: {}".format(access_times))
        if access_times:
            raise Exception("Extra accesses. Unmatched: {}".format(access_times))
