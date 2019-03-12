from random import randint

from ddt import ddt, data
import mpmath as mp
import numpy as np

from kaos.algorithm import view_cone
from kaos.errors import ViewConeError
from kaos.constants import SECONDS_PER_DAY, J2000
from kaos.tuples import Vector3D, TimeInterval
from kaos.models import Satellite
from kaos.utils import interval_utils
from kaos.models.parser import parse_ephemeris_file
from kaos.algorithm.coord_conversion import geod_to_geoc_lat, ecef_to_eci
from kaos.algorithm.interpolator import Interpolator
from .. import KaosTestCase


@ddt
class TestViewCone(KaosTestCase):
    """ Test cases for viewing cone algorithm"""

    @classmethod
    def setUpClass(cls):
        super(TestViewCone, cls).setUpClass()
        parse_ephemeris_file("ephemeris/Radarsat2.e")

    @data(('test/test_data/vancouver.test', (1514764800, 1514764800 + 11 * 24 * 3600), 10))
    def test_reduce_poi_with_access_file(self, test_data):
        """Test reduce_poi with access file"""

        access_file, interval, error_threshold = test_data
        interval = TimeInterval(*interval)

        # Get access information
        access_info = self.parse_access_file(access_file)
        trimmed_accesses = interval_utils.trim_poi_segments(access_info.accesses, interval)

        # Gather data for every 24 hour period of the input interval
        q_mag = Satellite.get_by_name(access_info.sat_name)[0].maximum_altitude
        sat_platform_id = Satellite.get_by_name(access_info.sat_name)[0].platform_id
        sat_irp = Interpolator(sat_platform_id)
        poi_list = [TimeInterval(start, start + 24 * 60 * 60) for start
                    in range(interval[0], interval[1], 24 * 60 * 60)]
        middle_time_list = [time.start + 12 * 60 * 60 for time in poi_list]
        sat_pos_ecef_list, sat_vel_ecef_list = map(list, zip(*[sat_irp.interpolate(t) for t in
                                                               middle_time_list]))
        sat_pos_list, sat_vel_list = ecef_to_eci(np.transpose(np.asarray(sat_pos_ecef_list)),
                                                 np.transpose(np.asarray(sat_vel_ecef_list)),
                                                 middle_time_list)

        # Run viewing cone
        reduced_poi_list = [reduced_poi for idx, poi in enumerate(poi_list) for reduced_poi in
                            view_cone.reduce_poi(access_info.target, sat_pos_list[idx],
                                                 sat_vel_list[idx], q_mag, poi)]

        reduced_poi_list = interval_utils.fuse_neighbor_intervals(reduced_poi_list)

        # Check coverage
        for poi in reduced_poi_list:
            trimmed_accesses = filter(lambda access: not(
                (poi.start - error_threshold < access.start) and
                (poi.end + error_threshold > access.end)),
                trimmed_accesses)
        if trimmed_accesses:
            print("Remaining accesses: ", trimmed_accesses)
            raise Exception("Some accesses are not covered")

    @data(
        # Test case with only 2 roots
        ((40, 80), (6.8779541256529745e+06, 4.5999490750985817e+04, 1.9992074250214235e+04),
         (-5.1646755701370530e+01, 5.3829730836383123e+03, 5.3826328640238344e+03),
         6878140 * (1 + 1.8e-16), TimeInterval(J2000 + 43200, J2000 + SECONDS_PER_DAY + 43200)),
        # Test case with no roots (always inside the viewing cone)
        ((0, 0), (7.3779408317663465e+06, 4.9343382472754820e+04, 2.1445380156320374e+04),
         (-5.0830385351827260e+01, 7.3220252051302523e+03, 6.4023511402880990e+02),
         7378140 * (1 + 1.8e-16), TimeInterval(J2000 + 43200, J2000 + SECONDS_PER_DAY + 43200))
    )
    def test_reduce_poi_unsupported_case(self, test_data):
        """Tests the viewing cone algorithm with unsupported configurations of orbit and location

        test_data format:
            site_lat_lon, sat_pos, sat_vel, q_magnitude, poi

        Values generated using: A Matlab implementation of viewing cone (using aerospace toolbox)
            which in turn was tested with STK
        """
        with self.assertRaises(ViewConeError):
            view_cone.reduce_poi(*test_data)

    def test_reduce_poi_input_error(self):
        """Tests whether reduce_poi can detect improper POI"""
        # Create an improperly ordered POI
        small = randint(1, 100000000)
        big = randint(1, 100000000)
        if big < small:
            big, small = small, big
        if big == small:
            big = big + 1
        improper_time = TimeInterval(J2000 + big, J2000 + small)

        with self.assertRaises(ValueError):
            view_cone.reduce_poi((0, 0), (0, 0, 0), (0, 0, 0), 0, improper_time)
