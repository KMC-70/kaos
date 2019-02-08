from ddt import ddt, data

from kaos.algorithm.visibility_finder import VisibilityFinder
from kaos.algorithm import view_cone
from kaos.tuples import TimeInterval
from kaos.models import Satellite
from kaos.models.parser import parse_ephemeris_file

import mpmath as mp
import numpy as np
from itertools import izip_longest
from . import KaosVisibilityFinderTestCase

@ddt
class TestVisibilityFinder(KaosVisibilityFinderTestCase):
    """Test the visibility finder's accuracy."""

    @classmethod
    def setUpClass(cls):
        super(TestVisibilityFinder, cls).setUpClass()
        parse_ephemeris_file("ephemeris/Radarsat2.e")

    @data(('test/algorithm/vancouver.test', (1514764800, 1514764800+5*24*60*60), 60))
    def test_full_visibility(self, test_data):
        """Tests that the visibility finder produces the same results as the access file.

        Args:
            test_data (tuple): A three tuple containing the:
                                1 - The path of KAOS access test file
                                2 - A tuple of the desired test duration
                                3 - The maximum tolerated deviation in seconds
        Note:
            Ranges provided must not start or end at an access boundary. This is a result of the
            strict checking method provided.
        """
        access_file, interval, max_error = test_data

        access_info = self.parse_access_file(access_file)
        finder = VisibilityFinder(Satellite.get_by_name(access_info.sat_name)[0].platform_id,
                                  access_info.target, interval)
        # access_times = np.asarray(finder.determine_visibility_brute_force_perf())
        access_times = np.asarray(finder.determine_visibility_perf())


        interval = TimeInterval(*interval)
        expected_accesses = view_cone._trim_poi_segments(access_info.accesses, interval)

        fail = False
        total_error = 0
        print ("=============================== visibility report ===============================")
        for exp_start, exp_end in expected_accesses:
            idx = (np.abs(np.transpose(access_times)[0] - exp_start)).argmin()
            error = abs(exp_start - access_times[idx][0]) + abs(exp_end - access_times[idx][1])
            if error > 600:
                fail = True
                print 'start, ',exp_start,',',"------------",',', mp.nstr(access_times[idx][0]-exp_start,6)
                print 'end,   ',exp_end,',',"------------",',', mp.nstr(access_times[idx][1]-exp_end,6)
            else:
                print 'start, ',exp_start,',',mp.nstr(access_times[idx][0],11),',', mp.nstr(access_times[idx][0]-exp_start,6)
                print 'end,   ',exp_end,',',mp.nstr(access_times[idx][1],11),',', mp.nstr(access_times[idx][1]-exp_end,6)
                total_error += error
                access_times = np.delete(access_times, idx, axis=0)

        print("\nTotal Error: {}".format(mp.nstr(total_error,12)))
        print("Average Error: {}".format(mp.nstr(total_error / (len(expected_accesses) * 2))))
        if fail:
            raise Exception("Missing accesses. Unmatched: {}".format(access_times))
        if len(access_times) != 0:
            raise Exception("Extra accesses. Unmatched: {}".format(access_times))

