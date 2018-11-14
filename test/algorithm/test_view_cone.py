import pytest, unittest

from ddt import ddt,data

from kaos.algorithm import view_cone, coord_conversion

# Time constants for test environment:
ONE_DAY = 86164 #23:56:04 in seconds
J2000 = 946684800 # Jan 1st 1970 in POSIX

@ddt
class TestViewCone(unittest.TestCase):

    @data(
        ((0,0),(7.3779408317663437e+06,4.9343382472754805e+04,2.1445380156320367e+04),
        (-2.1365998990816905e+01,2.2749470591161244e-01,7.3501075690228217e+03),7378140*(1+1.8e-19),
        2, 1.557161739571678e+05,1.843521229948921e+05,1.412700779528347e+05,1.987982189908994e+05),

        ((0,-110),(3.8947064924267233e+03,-3.1853237741789821e+03,-5.4020492601011592e+03),
        (-5.6110588908929424e+06,-4.4103685540919630e+06,-1.9375720842113465e+06),7478140*(1+0.05),
        0,2.027181145241799e+04,3.957976730797361e+04,-3.503052653228815e+03,6.335463139827675e+04)
    )
    def test__view_cone_calc(self,test_data):
        """Tests single calculations of viewing cone method

        test_data format:
          (site_lat, site_lon), sat_pos, sat_vel, q_magnitude ,m , expected a,expected b,
                expected c, expected d
        Values generated using: A Matlab implementation of viewing cone (using aerospace toolbox)
            which in turn was tested with STK
        """

        site_eci = coord_conversion.lla_to_eci(test_data[0][0], test_data[0][1], 0, 946684800)#J2000
        a,b,c,d = view_cone._view_cone_calc(site_eci,test_data[1],test_data[2],test_data[3],
                                                test_data[4])

        self.assertAlmostEqual(a, test_data[5], delta=5)
        self.assertAlmostEqual(b, test_data[6], delta=5)
        self.assertAlmostEqual(c, test_data[7], delta=5)
        self.assertAlmostEqual(d, test_data[8], delta=5)

    @data(
        ((0,0),(7.3779408317663437e+06,4.9343382472754805e+04,2.1445380156320367e+04),
        (-2.1365998990816905e+01,2.2749470591161244e-01,7.3501075690228217e+03),7378140*(1+1.8e-19),
        J2000,J2000+ONE_DAY,[(J2000+1.202394298942655e+04,J2000+2.647003898543385e+04),
        (J2000+5.510598795010193e+04,J2000+6.955208395443503e+04)]),

        ((0,-110),(3.8947064924267233e+03,-3.1853237741789821e+03,-5.4020492601011592e+03),
        (-5.6110588908929424e+06,-4.4103685540919630e+06,-1.9375720842113465e+06),7478140*(1+0.05),
        J2000,J2000+ONE_DAY,[(J2000,J2000+2.027181145241799e+04),(J2000+3.957976730797361e+04,
            J2000+6.335463139827675e+04),(J2000+8.266103734950394e+04,J2000+ONE_DAY)])
    )
    def test_view_cone(self,test_data):
        """Tests the public facing viewing cone algorithm

        test_data format:
         site lat&lon,sat_pos,sat_vel,q_magnitude,poi_start,poi_end,expected list of poi

        Values generated using: A Matlab implementation of viewing cone (using aerospace toolbox)
            which in turn was tested with STK
        """
        site_eci = coord_conversion.lla_to_eci(test_data[0][0], test_data[0][1], 0, 946684800)#J2000
        poi_list = view_cone.view_cone(site_eci,test_data[1],test_data[2],test_data[3],test_data[4],
                                            test_data[5])
        for answer,expected in zip(poi_list,test_data[6]):
            self.assertAlmostEqual(answer[0], expected[0], delta=5)
            self.assertAlmostEqual(answer[1], expected[1], delta=5)
