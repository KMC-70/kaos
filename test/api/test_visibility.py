"""Caching and History API test for KAOS."""


from collections import namedtuple
import re
import logging

from ddt import ddt, data, file_data

from kaos.algorithm.visibility_finder import VisibilityFinder
from kaos.models import Satellite
from kaos.models.parser import parse_ephemeris_file
from kaos.utils.time_conversion import utc_to_unix

from .. import KaosTestCase


@ddt
class TestVisibilityApi(KaosTestCase):
    """Test class for the history API."""
    @data(('test/test_data/vancouver.test', ('20180101T00:00:00.0', '20180101T02:00:00.0'), 60),
          ('test/test_data/vancouver.test', ('20180104T00:00:00.0', '20180107T11:59:59.0'), 60),
          ('test/test_data/vancouver.test', ('20180102T00:00:00.0', '20180102T11:59:59.0'), 60))
    def test_visibility(self, test_data):
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
        pass
        """
        access_file, interval, max_error = test_data

        posix_interval = (utc_to_unix(interval[0]), utc_to_unix(interval[1]))
        access_info = self.parse_access_file(access_file, posix_interval)
        satellite_id = Satellite.get_by_name(access_info.sat_name)[0].platform_id

        request = {'Target': access_info.target,
                   'POI': {'startTime': interval[0],
                           'endTime': interval[1]},
                   'PlatformID': [satellite_id]}

        with self.app.test_client() as client:
            response = client.post('/visibility/search', json=request)

        self.assertTrue(response.is_json)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json['Opportunities']), len(access_info.accesses))

        for oppertunity in response.json['Opportunities']:
            self.assertEqual(satellite_id, oppertunity['PlatformID'])
            predicted_access = (oppertunity['start_time'], oppertunity['end_time'])
            interval = posix_interval
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

    @file_data("test_data_visibility.json")
    def test_visibility_incorrect_input(self, Target, POI, PlatformID, Reasons):
        request = {'Target': Target,
                   'POI': POI,
                   'PlatformID': PlatformID}

        with self.app.test_client() as client:
            response = client.post('/visibility/search', json=request)

        logging.debug("Response was: %s\nCode: %s\n", response.json, response.status)

        self.assertTrue(response.is_json)
        self.assertEqual(response.status_code, 422)

        for reason in Reasons:
            if reason not in response.json["reasons"]:
                self.assertTrue(False, msg="Missing reason in response: {}".format(reason))


@ddt
class TestOpertunityApi(KaosTestCase):

    @classmethod
    def setUpClass(cls):
        """Add default test responses."""
        super(TestOpertunityApi, cls).setUpClass()
        parse_ephemeris_file("ephemeris/Radarsat2.e")

    @data(('test/test_data/vancouver_area.test', ('20180101T00:00:00.0', '20180102T00:00:00.0'),
           60),
          ('test/test_data/vancouver_area.test', ('20180103T00:00:00.0', '20180105T00:00:00.0'),
           60))
    def test_visibility(self, test_data):
        """Tests that the visibility finder produces the same results as the access file.

        Args:
            test_data (tuple): A three tuple containing the:
                                1 - The path of KAOS access test file
                                2 - A tuple of the desired POI
                                3 - The maximum tolerated deviation in seconds
        Note:
            Ranges provided must not start or end at an access boundary. This is a result of the
            strict checking method provided.
        """
        access_file, interval, max_error = test_data

        posix_interval = (utc_to_unix(interval[0]), utc_to_unix(interval[1]))
        access_info = self.parse_access_file(access_file, posix_interval)
        satellite_id = Satellite.get_by_name(access_info.sat_name)[0].platform_id
        request = {'TargetArea': access_info.target,
                   'POI': {
                        'startTime': interval[0],
                        'endTime': interval[1]},
                   'PlatformID': [satellite_id]}

        with self.app.test_client() as client:
            response = client.post('/opertunity/search', json=request)

        self.assertTrue(response.is_json)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json['Opportunities']), len(access_info.accesses))

        for oppertunity in response.json['Opportunities']:
            self.assertEqual(satellite_id, oppertunity['PlatformID'])
            predicted_access = (oppertunity['start_time'], oppertunity['end_time'])
            interval = posix_interval
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


