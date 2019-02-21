from ddt import ddt, data

from . import KaosVisibilityFinderTestCase
from kaos.algorithm.visibility_finder import VisibilityFinder
from kaos.algorithm.coord_conversion import ecef_to_eci
from kaos.algorithm import view_cone
from kaos.tuples import TimeInterval
from kaos.models import Satellite
from kaos.models.parser import parse_ephemeris_file
from kaos.algorithm.interpolator import Interpolator
from itertools import tee

import mpmath as mp
import numpy as np




@ddt
class TestVisibilityFinderPerf(KaosVisibilityFinderTestCase):
    """Test the visibility finder's accuracy."""
    @staticmethod
    def pairwise(iterable):
        """s -> (s0,s1), (s1,s2), (s2, s3), ... , (sn, None)"""
        iterable.append(None)
        a, b = tee(iterable)
        next(b, None)
        return zip(a, b)


    @classmethod
    def setUpClass(cls):
        super(TestVisibilityFinderPerf, cls).setUpClass()
        # import cProfile
        # import pstats
        # import sys
        # profile = cProfile.Profile()
        # profile.enable()
        parse_ephemeris_file("ephemeris/Radarsat2.e")
        # profile.disable()
        # stats = pstats.Stats(profile, stream=sys.stdout)
        # stats.strip_dirs().sort_stats('cumtime').print_stats(50)

    @data(('test/algorithm/vancouver.test', (1514764800, 1514764800 + 5 * 24 * 60 * 60)))
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
        interval = TimeInterval(interval[0], interval[1])
        access_info = self.parse_access_file(access_file)
        sat_id = Satellite.get_by_name(access_info.sat_name)[0].platform_id
        max_q = Satellite.get_by_name(access_info.sat_name)[0].maximum_altitude
        sat_irp = Interpolator(sat_id)
        print("\n")

        use_view_cone = True
        vectorized = True

        if use_view_cone is False:
            finder = VisibilityFinder(sat_id, access_info.target, interval)
            #NOTE: change to burte_force=True to switch to brute-force method.
            access_times = np.asarray(finder.profile_determine_visibility(brute_force=False))
        else:
            import cProfile
            import pstats
            import sys
            profile = cProfile.Profile()
            profile.enable()
            # Perf test zone

            ####################### vectorized
            if vectorized is True:
                poi_list = [TimeInterval(start,start+24*60*60) for start in range(interval[0], interval[1], 24*60*60)]
                sat_pos_ecef_list = []
                sat_vel_ecef_list = []
                middle_time_list = []
                for time in poi_list:
                    middle_time = time.start+12*60*60
                    sat_pos_ecef, sat_vel_ecef = sat_irp.interpolate(middle_time)
                    middle_time_list.append(middle_time)
                    sat_pos_ecef_list.append(sat_pos_ecef)
                    sat_vel_ecef_list.append(sat_vel_ecef)


                sat_pos_list, sat_vel_list = ecef_to_eci(np.transpose(np.asarray(sat_pos_ecef_list)),
                                                         np.transpose(np.asarray(sat_vel_ecef_list)),
                                                         middle_time_list)

                reduced_poi_list = []
                for idx,poi in enumerate(poi_list):
                    reduced_poi_list.extend(view_cone.reduce_poi(access_info.target, sat_pos_list[idx],
                                                                 sat_vel_list[idx], max_q, poi))
            ####################### NON vectorized
            else:
                reduced_poi_list = []
                for start_time in range(interval[0], interval[1], 24*60*60):
                    poi = TimeInterval(start_time, start_time+24*60*60)
                    # get sat at start_time
                    sat_pos_ecef, sat_vel_ecef = sat_irp.interpolate(start_time+12*60*60)
                    sat_pos, sat_vel = ecef_to_eci(np.asarray(sat_pos_ecef), np.asarray(sat_vel_ecef), start_time+12*60*60)

                    reduced_poi_list.extend(view_cone.reduce_poi(access_info.target, sat_pos[0], sat_vel[0], max_q, poi))

            ###################### END

            reduced_poi_list = view_cone._trim_poi_segments(reduced_poi_list, interval)
            reduced_poi_list.sort(key=lambda x: x.start)

            # for i in reduced_poi_list:
            #     print("start : {}, end {}".format(mp.nstr(i[0],12),mp.nstr(i[1],12)))

            skip_next = False
            reduced_time = 0
            trimmed_reduced_poi_list = []
            for i, j in self.pairwise(reduced_poi_list):
                if skip_next is True:
                    skip_next = False
                    continue
                if j is not None and i[1] == j[0]:
                    trimmed_reduced_poi_list.append(TimeInterval(mp.nint(i[0]),mp.nint(j[1])))
                    reduced_time += abs(mp.nint(j[1])-mp.nint(i[0]))
                    skip_next = True
                else:
                    trimmed_reduced_poi_list.append(TimeInterval(mp.nint(i[0]),mp.nint(i[1])))
                    reduced_time += abs(mp.nint(i[1])-mp.nint(i[0]))

            print("reduced time is: {}".format(mp.nstr(reduced_time,12)))
            print("input   time is: {}".format(interval[1]-interval[0]))

            # for i in trimmed_reduced_poi_list:
            #     print("start : {}, end {}".format(mp.nstr(i[0],15),mp.nstr(i[1],15)))

            access_times = []
            for reduced_poi in trimmed_reduced_poi_list:
                finder = VisibilityFinder(sat_id, access_info.target, reduced_poi)
                access_times.extend(np.asarray(finder.determine_visibility()))

            # End of perf test zone
            profile.disable()
            stats = pstats.Stats(profile, stream=sys.stdout)
            stats.strip_dirs().sort_stats('cumtime').print_stats(50)

        interval = TimeInterval(*interval)
        expected_accesses = view_cone._trim_poi_segments(access_info.accesses, interval)

        # print ("len of access ",len(access_times))
        # print ("len of expected_accesses", len(expected_accesses))

        # while len(access_times) < len(expected_accesses):
        #     access_times.append(TimeInterval(0,0))

        fail = False
        total_error = 0
        print ("=============================== visibility report ===============================")
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
        if len(access_times) != 0:
            raise Exception("Extra accesses. Unmatched: {}".format(access_times))
