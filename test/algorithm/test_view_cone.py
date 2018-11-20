import pytest, unittest

from random import randint

from ddt import ddt, data

from kaos.algorithm import view_cone
from kaos.errors import ViewConeError
from kaos.constants import SECONDS_PER_DAY, J2000
from kaos.tuples import Vector3D, TimeInterval

@ddt
class TestViewCone(unittest.TestCase):
    """ Test cases for viewing cone algorithm"""
    @data(
        (Vector3D(x=-1104185.9192367536, y=6281831.34325032, z=147.06403560447933),
         (7.3779408317663437e+06, 4.9343382472754805e+04, 2.1445380156320367e+04),
         (-2.1365998990816905e+01, 2.2749470591161244e-01, 7.3501075690228217e+03),
         7378140*(1+1.8e-19), 2, 1.557161739571678e+05, 1.843521229948921e+05, 1.412700779528347e+05
         , 1.987982189908994e+05),

        (Vector3D(x=6280644.383697788, y=-1110917.500932147, z=149.53109223909593),
         (3.8947064924267233e+03, -3.1853237741789821e+03, -5.4020492601011592e+03),
         (-5.6110588908929424e+06, -4.4103685540919630e+06, -1.9375720842113465e+06),
         7478140*(1+0.05), 0, 2.027181145241799e+04, 3.957976730797361e+04, -3.503052653228815e+03,
         6.335463139827675e+04)
    )
    def test__view_cone_calc(self, test_data):
        """Tests single calculations of viewing cone method

        test_data format:
          (site_lat, site_lon), sat_pos, sat_vel, q_magnitude ,m , expected a,expected b,
                expected c, expected d
        Values generated using: A Matlab implementation of viewing cone (using aerospace toolbox)
            which in turn was tested with STK
        """
        t_1, t_2, t_3, t_4 = view_cone._view_cone_calc(test_data[0], test_data[1], test_data[2],
                                                       test_data[3], test_data[4])

        self.assertAlmostEqual(t_1, test_data[5], delta=5)
        self.assertAlmostEqual(t_2, test_data[6], delta=5)
        self.assertAlmostEqual(t_3, test_data[7], delta=5)
        self.assertAlmostEqual(t_4, test_data[8], delta=5)

    @data(
        (Vector3D(x=-1104185.9192367536, y=6281831.34325032, z=147.06403560447933),
         (7.3779408317663437e+06, 4.9343382472754805e+04, 2.1445380156320367e+04),
         (-2.1365998990816905e+01, 2.2749470591161244e-01, 7.3501075690228217e+03),
         7378140*(1+1.8e-19), TimeInterval(J2000, J2000+SECONDS_PER_DAY),
         [(J2000+1.202394298942655e+04, J2000+2.647003898543385e+04),
          (J2000+5.510598795010193e+04, J2000+6.955208395443503e+04)]),

        (Vector3D(x=6280644.383697788, y=-1110917.500932147, z=149.53109223909593),
         (3.8947064924267233e+03, -3.1853237741789821e+03, -5.4020492601011592e+03),
         (-5.6110588908929424e+06, -4.4103685540919630e+06, -1.9375720842113465e+06),
         7478140*(1+0.05), TimeInterval(J2000, J2000+SECONDS_PER_DAY),
         [(J2000, J2000+2.027181145241799e+04),
          (J2000+3.957976730797361e+04, J2000+6.335463139827675e+04),
          (J2000+8.266103734950394e+04, J2000+SECONDS_PER_DAY)])
    )
    def test_reduce_poi(self, test_data):
        """Tests the viewing cone algorithm with non-corner-case data

        test_data format:
         site lat&lon,sat_pos,sat_vel,q_magnitude,poi,expected list of poi

        Values generated using: A Matlab implementation of viewing cone (using aerospace toolbox)
            which in turn was tested with STK
        """
        poi_list = view_cone.reduce_poi(test_data[0], test_data[1], test_data[2], test_data[3],
                                        test_data[4])
        for answer, expected in zip(poi_list, test_data[5]):
            self.assertAlmostEqual(answer.start, expected[0], delta=5)
            self.assertAlmostEqual(answer.end, expected[1], delta=5)

    @data(
        # Test case with only 2 roots
        (Vector3D(x=-4892824.52928303, y=2505.6040609508723, z=4077844.5084031746),
         (6.8779541256529745e+06, 4.5999490750985817e+04, 1.9992074250214235e+04),
         (-5.1646755701370530e+01, 5.3829730836383123e+03, 5.3826328640238344e+03),
         6878140*(1+1.8e-16), TimeInterval(J2000, J2000+SECONDS_PER_DAY)),
        # Test case with no roots (always inside the viewing cone)
        (Vector3D(x=-1104185.9192367536, y=6281831.34325032, z=147.06403560447933),
         (7.3779408317663465e+06, 4.9343382472754820e+04, 2.1445380156320374e+04),
         (-5.0830385351827260e+01, 7.3220252051302523e+03, 6.4023511402880990e+02),
         7378140*(1+1.8e-16), TimeInterval(J2000, J2000+SECONDS_PER_DAY))
    )
    def test_reduce_poi_unsupported_case(self, test_data):
        """Tests the viewing cone algorithm with unsupported configurations of orbit and location

        test_data format:
         site lat&lon,sat_pos,sat_vel,q_magnitude,poi

        Values generated using: A Matlab implementation of viewing cone (using aerospace toolbox)
            which in turn was tested with STK
        """
        with self.assertRaises(ViewConeError):
            view_cone.reduce_poi(test_data[0], test_data[1], test_data[2], test_data[3],
                                 test_data[4])

    def test_reduce_poi_input_error(self):
        """Tests whether reduce_poi can detect improper POI"""
        # Create an improperly ordered POI
        small = randint(1, 100000000)
        big = randint(1, 100000000)
        if big < small:
            big, small = small, big
        if big == small:
            big = big + 1
        improper_time = TimeInterval(J2000+big, J2000+small)

        with self.assertRaises(ValueError):
            view_cone.reduce_poi((0, 0, 0), (0, 0, 0), (0, 0, 0), 0, improper_time)
