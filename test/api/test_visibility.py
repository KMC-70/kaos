"""Caching and History API test for KAOS."""


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
class TestVisibilityApi(KaosTestCase):
    """Test class for the history API."""

    @classmethod
    def setUpClass(cls):
        """Add default test responses."""
        super(TestVisibilityApi, cls).setUpClass()
        parse_ephemeris_file("ephemeris/Radarsat2.e")

    # pylint: disable=line-too-long
    @staticmethod
    def parse_access_file(file_path, access_range=None):
        """Reads a KAOS access test file, these files follow the following format:

            ====================================================================================================
            Satellite Name: <Sat Name>
            Target Point: <lon>, <lat>
            ====================================================================================================
            record number, access start, access_end, access_duration
            ....

        Args:
            file_path (string): The path of the KAOS access test file.
            access_range (tuple):

        Returns:
            An AccessTestInfo tuple.
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
            if (access_range is None
                or ((start_time >= access_range[0] and start_time <= access_range[1]) or
                    (end_time >= access_range[0] and end_time <= access_range[1]) or
                    (start_time <= access_range[0] and end_time >= access_range[0]) or
                    (end_time <= access_range[1] and end_time >= access_range[1]))):
                accesses.append((start_time, end_time))

        return AccessTestInfo(sat_name, target, accesses)
    # pylint: enable=line-too-long

    @data(('test/algorithm/vancouver.test', ('20180101T00:00:00.0', '20180101T02:00:00.0'), 60))
    def test_full_visibility(self, test_data):
        """Tests that the visibility finder produces the same results as the access file.

        Args:
            test_data (tuple): A three tuple containing the:
                                1 - The path of KAOS access test file
                                2 - A tuple of the desired test duration
                                3 - The maximum tolerated deviation in seconds
        Note:
            Ranges provided must not start or end at an access boundary. This is a result of the
            strict checking method provided.
        """
        access_file, interval, max_error = test_data
        posix_interval = (utc_to_unix(interval[0]), utc_to_unix(interval[1]))

        access_info = self.parse_access_file(access_file, posix_interval)

        request = {'Target': access_info.target,
                   'POI': {'startTime': interval[0],
                           'endTime': interval[1]},
                   'PlatformID': 1}
        with self.app.test_client() as client:
            response = client.post('/visibility/search', json=request)

        self.assertTrue(response.is_json)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json['Opportunities']), len(access_info.accesses))

        
        """
        for predicted_access in access_times:
            found = False
            for actual_access in access_info.accesses:
                if (interval[0] > actual_access[0]) and (interval[1] < actual_access[1]):
                    if ((abs(interval[0] - predicted_access[0]) < max_error) and
                            (abs(interval[1] - predicted_access[1]) < max_error)):
                        found = True
                        break
                if interval[0] > actual_access[0]:
                    if ((abs(interval[0] - predicted_access[0]) < max_error) and
                            (abs(actual_access[1] - predicted_access[1]) < max_error)):
                        found = True
                        break
                elif interval[1] < actual_access[1]:
                    if ((abs(actual_access[0] - predicted_access[0]) < max_error) and
                            (abs(interval[1] - predicted_access[1]) < max_error)):
                        found = True
                        break

                if ((abs(actual_access[0] - predicted_access[0]) < max_error) and
                        (abs(actual_access[1] - predicted_access[1]) < max_error)):
                    found = True
                    break

            if not found:
                raise Exception('Wrong access: {}'.format(predicted_access))
        """
