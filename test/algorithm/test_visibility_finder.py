"""Testing the visibility_finder."""
from kaos.algorithm.coord_conversion import lla_to_eci
from kaos.algorithm.visibility_finder import VisibilityFinder
from kaos.models import DB, Satellite, ResponseHistory, OrbitSegment, OrbitRecord
from kaos.models.parser import *
import numpy as np
import unittest
from mock import patch
from .. import KaosTestCase
from kaos.algorithm.interpolator import Interpolator

class TestVisibilityFinder(KaosTestCase):
    @patch('kaos.algorithm.interpolator.Interpolator.interpolate', return_value=
    ((-6.9980497691646582e+06, -1.4019786400312854e+06, 7.0754554424135364e+05),
     (-9.4202033738527109e+02, 9.5296010534027573e+02, -7.3355694593015414e+03)))
    def test_visibility(self, interpolate):
        # testing point r_site (the coordinates(Lat, Longi, r_earth, epoch_time_J2000) of vancouver
        # generated from STK)
        r_site_spherical = (49.07, -123.113, 0, 946684800)
        # convert to eci since r_sat and v_sat are in eci(J2000) (Assume lla_to_eci works correctly)
        r_site = lla_to_eci(*r_site_spherical)[0]
        # testing point r_sat and v_sat(the first line in Radarsat2_J2000.e under ephemeris)
        r_sat = (-6.9980497691646582e+06, -1.4019786400312854e+06, 7.0754554424135364e+05)
        delta_r = np.subtract(r_sat, r_site)
        r_site_0 = r_site / np.linalg.norm(delta_r)

        visibility = np.dot(delta_r, r_site_0) / np.linalg.norm(r_site)
        finder = VisibilityFinder(1, (49.07, -123.113), (946684800, 0))
        self.assertAlmostEqual(finder.visibility(946684800), visibility)

    @patch('kaos.algorithm.interpolator.Interpolator.interpolate', return_value=
    ((-6.9980497691646582e+06, -1.4019786400312854e+06, 7.0754554424135364e+05),
     (-9.4202033738527109e+02, 9.5296010534027573e+02, -7.3355694593015414e+03)))
    def test_visibility_first_derivative(self, interpolate):
        # testing point r_site (the coordinates(Lat, Longi, r_earth, epoch_time_J2000) of vancouver
        # generated from STK)
        r_site_spherical = (49.07, -123.113, 0, 946684800)
        # convert to eci since r_sat and v_sat are in eci(J2000) (Assume lla_to_eci works correctly)
        r_site, v_site = lla_to_eci(*r_site_spherical)

        # testing point r_sat and v_sat(the first line in Radarsat2_J2000.e under ephemeris)
        r_sat = (-6.9980497691646582e+06, -1.4019786400312854e+06, 7.0754554424135364e+05)
        v_sat = (-9.4202033738527109e+02, 9.5296010534027573e+02, -7.3355694593015414e+03)

        delta_r = np.subtract(r_sat, r_site)
        r_site_0 = r_site/np.linalg.norm(r_site)
        delta_r_prime = np.subtract(v_sat, v_site)

        #not sure about r_site_0_prime
        r_site_0_prime = v_site/np.linalg.norm(v_site)
        visibility_prime = (1/np.linalg.norm(delta_r)) * (np.dot(delta_r_prime, r_site_0) +
                                                          np.dot(delta_r, r_site_0_prime))\
                           -(1/(np.linalg.norm(delta_r))**3) * \
                           np.dot(np.dot(delta_r, delta_r_prime)*delta_r,r_site_0)

        finder = VisibilityFinder(1,(49.07, -123.113), (946684800,0))
        self.assertAlmostEqual(finder.visibility_first_derivative(946684800), visibility_prime)

    def test_vis(self):
        parse_ephemeris_file("ephemeris/Radarsat2_J2000.e")
        #x = VisibilityFinder(1, (49.07, -123.113), (1514764800,1514775600))
        x = VisibilityFinder(1, (49.07, -123.113), (1514768280,1514775600))
        y = x.find_approx_coeffs(1514764800,1514764801)
        import pdb; pdb.set_trace()


