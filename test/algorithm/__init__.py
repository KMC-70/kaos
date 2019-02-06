import os, sys

from .. import KaosTestCase
from collections import namedtuple
import re

from ddt import ddt, data

from kaos.models import Satellite
from kaos.utils.time_conversion import utc_to_unix

sys.path.insert(0, os.path.abspath('../..'))
sys.path.insert(0, os.path.abspath('../../kaos'))

AccessTestInfo = namedtuple('AccessTestInfo', 'sat_name, target, accesses')

@ddt
class KaosVisibilityFinderTestCase(KaosTestCase):
    """Parent class for Testing the visibility finder using specialized test files.
    These files are generated from STK and modified to include all relevant data about actual
    expected access times.
    """

    @classmethod
    def setUpClass(cls):
        super(KaosVisibilityFinderTestCase, cls).setUpClass()

    # pylint: disable=line-too-long
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
            accesses.append((start_time, end_time))

        return AccessTestInfo(sat_name, target, accesses)
    # pylint: enable=line-too-long
