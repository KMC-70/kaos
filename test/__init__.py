"""Defines the base classes to be used in testing KAOS."""

import os, sys
import re
from unittest import TestCase
from collections import namedtuple

from ddt import ddt, data

sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('../kaos'))

import kaos
from kaos import create_app
from kaos.models import DB, Satellite
from kaos.tuples import TimeInterval
from kaos.utils.time_conversion import utc_to_unix

AccessTestInfo = namedtuple('AccessTestInfo', 'sat_name, target, accesses')

@ddt
class KaosTestCase(TestCase):
    """Test class that provides DB setup and teardown at the beginning and end of a test case.

    Additionalli, this class provides mechanisms for testing the visibility using specialized test
    files. These files are generated from STK and modified to include all relevant data about actual
    expected access times.
    """

    @staticmethod
    def create_app():
        return create_app("settings_test.cfg")

    @classmethod
    def setUpClass(cls):
        cls.app = KaosTestCase.create_app()
        cls.client = cls.app.test_client()

        cls.app.app_context().push()
        DB.create_all()

    @classmethod
    def tearDownClass(cls):
        DB.session.rollback()
        DB.session.commit()
        DB.session.remove()
        DB.drop_all()

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

        Returns:
            An AccessTestInfo tuple.
        """
        with open(file_path) as access_file:
            access_info_text = access_file.read()

        section_regex = re.compile(r'={99}', re.MULTILINE)
        access_info = section_regex.split(access_info_text)

        # Parse the header
        sat_name = re.search(r'Satellite Name: ([a-zA-Z0-9_]+)', access_info[1]).groups()[0]
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
                accesses.append(TimeInterval(start_time, end_time))

        return AccessTestInfo(sat_name, target, accesses)
    # pylint: enable=line-too-long


class KaosTestCaseNonPersistent(KaosTestCase):
    """Test classes subclassing this class will have the DB recreated in between each test."""

    def setUp(self):
        DB.create_all()

    def tearDown(self):
        DB.session.rollback()
        DB.session.commit()
        DB.drop_all()
