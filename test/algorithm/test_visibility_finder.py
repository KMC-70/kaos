"""Testing the visibility_finder."""
from kaos.algorithm.coord_conversion import *
from kaos.algorithm.visibility_finder import *
import numpy as np
import unittest

class TestVisibilityFinder():
    def test_first_derivative(self):
        # testing point r_site (the coordinates(Lat, Longi, r_earth, epoch_time_J2000) of vancouver
        # generated from STK)
        r_site_spherical = (49.07, -123.113, 6365930, 946684800)
        # convert to eci since r_sat and v_sat are in eci(J2000) (Assume lla_to_eci works correctly)
        r_site_cart = lla_to_eci(r_site_spherical[0],r_site_spherical[1],r_site_spherical[2],
                                 r_site_spherical[3])
        r_site = r_site_cart[0]
        v_site = r_site_cart[1]
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
        #self.assertAlmostEqual(satallite_visibility_derivative(),visibility_prime)
        #import pdb; pdb.set_trace()


