"""satellites API test for KAOS."""

import json

from kaos.models import DB, Satellite
from kaos.models.parser import parse_ephemeris_file
from .. import KaosTestCase

class TestSatellitesApi(KaosTestCase):
    """Test class for the satellites API."""

    @classmethod
    def setUpClass(cls):
        """Add default test responses."""
        super(TestSatellitesApi, cls).setUpClass()
        parse_ephemeris_file("ephemeris/Aqua_27424.e")
        parse_ephemeris_file("ephemeris/Radarsat2.e")
        parse_ephemeris_file("ephemeris/Rapideye2_33312.e")
        cls.response_data = '[{"id": 1, "satellite_name": "Aqua_27424"}, ' \
                             '{"id": 2, "satellite_name": "Radarsat2"}, ' \
                             '{"id": 3, "satellite_name": "Rapideye2_33312"}]'


    def test_get_response_correct(self):
        """Test that a valid request can be processed successfully."""
        # import pdb;pdb.set_trace()
        with self.app.test_client() as client:
            response = client.get('/satellites')
            self.assertEqual(response.status_code, 200, "Got unexpected status code")
            self.assertEqual(json.dumps(response.json), self.response_data,
                             "Got unexpected response data")

    def test_get_response_wrong_spelling(self):
        """Test that an invalid id type request will return the inappropriate error."""
        with self.app.test_client() as client:
            response = client.get('/satelllite')
            # import pdb;pdb.set_trace()
            self.assertEqual(response.status_code, 404, "Got unexpected status code")
            expected_response = ('{"reason": "404 Not Found: The requested URL was not found on '
                                 'the server.  If you entered the URL manually please check your '
                                 'spelling and try again."}')
            self.assertEqual(json.dumps(response.json), expected_response,
                             "Got unexpected response data")
