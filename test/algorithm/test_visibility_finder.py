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

    @data(('test/algorithm/vancouver.test', (1514764802, 1514772000), 60))
    def test_visibility(self, test_data):
        access_file, interval, max_error = test_data

        access_info = self.parse_access_file(access_file)
        finder = VisibilityFinder(1, access_info.target, interval)
        access_times = finder.determine_visibility()

        def check_access(predicted_time):
            accesses = filter(lambda time: abs(time[0] - predicted_time[0]) < max_error and
                                           abs(time[1] - predicted_time[1]) < max_error,
                               access_info.accesses)
            return accesses is True

        for access in access_times:
            if check_access(access):
                raise Exception('Wrong access: {}'.format(access))
