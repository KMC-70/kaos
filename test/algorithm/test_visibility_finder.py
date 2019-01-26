"""Testing the visibility_finder."""
from kaos.algorithm.coord_conversion import lla_to_eci
from kaos.algorithm.visibility_finder import VisibilityFinder
from kaos.models import DB, Satellite, ResponseHistory, OrbitSegment, OrbitRecord
from kaos.models.parser import *
import numpy as np
import unittest
from mock import patch
from ddt import ddt,data
from .. import KaosTestCase
from kaos.algorithm.interpolator import Interpolator
import re
from kaos.utils.time_conversion import utc_to_unix
from collections import namedtuple

AccessTestInfo = namedtuple('AccessTestInfo', 'sat_name, target, accesses')

@ddt
class TestVisibilityFinder(KaosTestCase):
    """Test the visibility finder using specialized test files. These files are generatef from STK
    and modified to include all relavent data"""

    @classmethod
    def setUpClass(cls):
        super(TestVisibilityFinder, cls).setUpClass()
        parse_ephemeris_file("ephemeris/Radarsat2_J2000.e")

    @staticmethod
    def parse_access_file(file_path):
        """Reads an access file."""
        with open(file_path) as f:
            access_info_text = f.read()


        section_regex = re.compile(r'={99}', re.MULTILINE)
        access_info = section_regex.split(access_info_text)

        # Parse the header
        sat_name = re.search(r'Satellite Name: ([a-zA-Z0-9]+)', access_info[1]).groups()[0]
        target = [float(point) for point in
                  re.search(r'Target Point: (.*)', access_info[1]).groups()[0].split(',')]
        # Parse the access times
        accesses = []
        raw_access_data = access_info[2].splitlines()
        for access in raw_access_data[1:]:
            access = access.split(',')
            # Parse the start and end time
            start_time = utc_to_unix(access[1].rstrip().lstrip(), '%d %b %Y %H:%M:%S.%f')
            end_time = utc_to_unix(access[2].rstrip().lstrip(), '%d %b %Y %H:%M:%S.%f')
            accesses.append((start_time, end_time))

        return AccessTestInfo(sat_name, target, accesses)
    """
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
    """

    #@data(('test/algorithm/vancouver.test',(1514764802,1514822400),60))
    @data(('test/algorithm/vancouver.test', (1514764802,1514772000), 60))
    def test_visibility(self, test_data):
        access_file, interval, max_error = test_data

        access_info = self.parse_access_file(access_file)
        finder = VisibilityFinder(1, access_info.target, interval)
        access_times = finder.determine_visibility()

        def check_access(predicted_time):
            accesses = filter( lambda time: abs(time[0] - predicted_time[0]) < max_error and
                                            abs(time[1] - predicted_time[1]) < max_error,
                               access_info.accesses)
            return accesses is True

        for access in access_times:
            if check_access(access):
                raise Exception('Wrong access: {}'.format(access))
