"""Testing the visibility_finder."""
from collections import namedtuple
import re

from ddt import ddt, data

from kaos.algorithm.visibility_finder import VisibilityFinder
from kaos.models import Satellite
from kaos.models.parser import parse_ephemeris_file
from kaos.utils.time_conversion import utc_to_unix

from .. import KaosTestCase

AccessTestInfo = namedtuple('AccessTestInfo', 'sat_name, target, accesses')

@ddt
class TestVisibilityFinder(KaosTestCase):
    """Test the visibility finder using specialized test files. These files are generated from STK
    and modified to include all relevant data about actual expected access times.
    """

    @classmethod
    def setUpClass(cls):
        super(TestVisibilityFinder, cls).setUpClass()
        parse_ephemeris_file("ephemeris/Radarsat2.e")

    #pylint: disable=line-too-long
    @staticmethod
    def parse_access_file(file_path):
        """Reads a KAOS access test file, these files follow the following format:

            ====================================================================================================
            Satellite Name: <Sat Name>
            Target Point: <lon>, <lat>
            ====================================================================================================
            record number, access start, access_end, access_duration
            ....

        Args:
            file_path (string): The path of the KAOS access test file.

        Returns:
            An AccessTestInfo tule
        """
        with open(file_path) as access_file:
            access_info_text = access_file.read()


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
    #pylint: enable=line-too-long

    @data(('test/algorithm/vancouver.test', (1514764802, 1514772000), 60),
          ('test/algorithm/vancouver.test', (1515160800, 1515164400), 60),
          ('test/algorithm/vancouver.test', (1515283201, 1515369540), 60))
    def test_visibility(self, test_data):
        """Tests that the visibility finder produces the same results as the access file.

        Args:
            test_data (tuple): A three tuple containing the:
                                1 - The path of KAOS access test file
                                2 - A tuple of the desired test duration
                                3 - The maximum tolerated deviation in seconds
        """
        access_file, interval, max_error = test_data

        access_info = self.parse_access_file(access_file)
        finder = VisibilityFinder(Satellite.get_by_name(access_info.sat_name)[0].platform_id,
                                  access_info.target, interval)
        access_times = finder.determine_visibility()

        #pylint: disable=deprecated-lambda,missing-docstring
        def check_access(predicted_time):
            accesses = filter(lambda time: abs(time[0] - predicted_time[0]) < max_error and
                              abs(time[1] - predicted_time[1]) < max_error,
                              access_info.accesses)
            return accesses is True
        #pylint: enable=deprecated-lambda,missing-docstring

        for access in access_times:
            if check_access(access):
                raise Exception('Wrong access: {}'.format(access))
