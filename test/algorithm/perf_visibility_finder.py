"""Visibility Finder Test File."""

from __future__ import print_function
import mpmath as mp
import numpy as np

from ddt import ddt, data

from kaos.algorithm.visibility_finder import VisibilityFinder
from kaos.algorithm.coord_conversion import ecef_to_eci
from kaos.algorithm import view_cone
from kaos.utils import interval_utils
from kaos.tuples import TimeInterval
from kaos.models import Satellite
from kaos.models.parser import parse_ephemeris_file
from kaos.algorithm.interpolator import Interpolator
from .. import KaosTestCase


@ddt
class TestVisibilityFinderPerf(KaosTestCase):
    """Test the visibility finder's accuracy."""

    @classmethod
    def setUpClass(cls):
        super(TestVisibilityFinderPerf, cls).setUpClass()
        parse_ephemeris_file("ephemeris/Radarsat2.e")
        # parse_ephemeris_file("ephemeris/Aqua_27424.e")
        # parse_ephemeris_file("ephemeris/Rapideye2_33312.e")
        # parse_ephemeris_file("ephemeris/TanSuo1_28220.e")
        # parse_ephemeris_file("ephemeris/Terra_25994.e")
        # parse_ephemeris_file("ephemeris/Worldview1_32060.e")

    @data(('test/test_data/vancouver.test', (1514764800, 1514764800 + 10 * 24 * 60 * 60)))
    # @data(('test/test_data/Aqua_vancouver.test', (1514764800, 1514764800 + 10 * 24 * 60 * 60)))
    # @data(('test/test_data/Rapideye2_vancouver.test', (1514764800, 1514764800 + 10 * 24 * 60 * 60)))
    # @data(('test/test_data/TanSuo1_vancouver.test', (1514764800, 1514764800 + 10 * 24 * 60 * 60)))
    # @data(('test/test_data/Terra_vancouver.test', (1514764800, 1514764800 + 10 * 24 * 60 * 60)))
    # @data(('test/test_data/Worldview1_vancouver.test', (1514764800, 1514764800 + 10 * 24 * 60 * 60)))
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
        # Use viewing cone algorithm or not
        use_view_cone = True
        # Do viewing cone coordinate conversion in series or as a vector
        vectorized = True

        access_file, interval = test_data
        interval = TimeInterval(interval[0], interval[1])
        access_info = self.parse_access_file(access_file)
        sat_id = Satellite.get_by_name(access_info.sat_name)[0].platform_id
        max_q = Satellite.get_by_name(access_info.sat_name)[0].maximum_altitude
        sat_irp = Interpolator(sat_id)
        print("\n")

        if use_view_cone is False:
            finder = VisibilityFinder(sat_id, access_info.target, interval)
            # NOTE: change to burte_force=True to switch to brute-force method.
            access_times = np.asarray(finder.profile_determine_visibility(brute_force=False))
        else:
            import cProfile
            import pstats
            import sys
            profile = cProfile.Profile()
            profile.enable()

            # Vectorized
            if vectorized is True:
                poi_list = [TimeInterval(start, start + 24 * 60 * 60) for start
                            in range(interval[0], interval[1], 24 * 60 * 60)]

                sampling_time_list = [time.start for time in poi_list]
                sampling_time_list.append(interval[1])
                sat_pos_ecef_list, sat_vel_ecef_list = map(list, zip(*[sat_irp.interpolate(t) for
                                                                       t in sampling_time_list]))

                sat_position_velocity_pairs = ecef_to_eci(
                                                np.transpose(np.asarray(sat_pos_ecef_list)),
                                                np.transpose(np.asarray(sat_vel_ecef_list)),
                                                sampling_time_list)

                reduced_poi_list = [reduced_poi for idx, poi in enumerate(poi_list) for reduced_poi
                                    in view_cone.reduce_poi(access_info.target,
                                                            sat_position_velocity_pairs[idx:idx+2],
                                                            max_q, poi)]
            # NON vectorized
            else:
                reduced_poi_list = []
                for start_time in range(interval[0], interval[1], 24 * 60 * 60):
                    poi = TimeInterval(start_time, start_time + 24 * 60 * 60)
                    # get sat at start_time
                    sat_pos_ecef, sat_vel_ecef = sat_irp.interpolate(start_time + 12 * 60 * 60)
                    sat_pos, sat_vel = ecef_to_eci(np.asarray(sat_pos_ecef),
                                                   np.asarray(sat_vel_ecef),
                                                   start_time + 12 * 60 * 60)

                    reduced_poi_list.extend(view_cone.reduce_poi(access_info.target, sat_pos[0],
                                                                 sat_vel[0], max_q, poi))

            trimmed_reduced_poi_list = interval_utils.fuse_neighbor_intervals(reduced_poi_list)

            access_times = []
            for reduced_poi in trimmed_reduced_poi_list:
                finder = VisibilityFinder(sat_id, access_info.target, reduced_poi)
                access_times.extend(np.asarray(finder.determine_visibility()))

            profile.disable()
            stats = pstats.Stats(profile, stream=sys.stdout)
            stats.strip_dirs().sort_stats('cumtime').print_stats(50)

            reduced_time = 0
            for time in trimmed_reduced_poi_list:
                reduced_time += time[1] - time[0]
            print("Viewing cone stats:")
            print("Reduced time is: {}".format(mp.nstr(reduced_time,12)))
            print("Input   time is: {}".format(interval[1]-interval[0]))

        interval = TimeInterval(*interval)
        expected_accesses = interval_utils.trim_poi_segments(access_info.accesses, interval)

        # Check the visibility times
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
        if access_times.size > 0:
            raise Exception("Extra accesses. Unmatched: {}".format(access_times))
