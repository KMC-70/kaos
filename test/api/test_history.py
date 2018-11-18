"""Caching and History API test for KAOS."""

import json

import context
from kaos.models import DB, ResponseHistory

from .. import KaosTestCase

class TestHistoryApi(KaosTestCase):
    """Test class for the history API."""

    @classmethod
    def setUpClass(cls):
        """Add default test responses."""
        KaosTestCase.setUpClass()

        cls.response_data = '{"working": "true"}'
        cls.response = ResponseHistory(cls.response_data)
        cls.response.save()

        DB.session.commit()

    def test_get_response_correct(self):
        """Test that a valid request can be processed successfully."""
        with self.app.test_client() as client:
            response = client.get('/search/{}'.format(self.response.uid))
            self.assertEqual(response.status_code, 200, "Got unexpected status code")
            self.assertEqual(json.dumps(response.json), self.response_data,
                             "Got unexpected response data")


    def test_get_response_incorrect_id(self):
        """Test that an invalid id request will return the inappropriate error."""
        with self.app.test_client() as client:
            response = client.get('/search/100')
            self.assertEqual(response.status_code, 404, "Got unexpected status code")
            expected_response = ('{"reasons": {"history_id": "Entry with value: 100 '
                                 'not found"}, "extra_info": {}}')
            self.assertEqual(json.dumps(response.json), expected_response,
                             "Got unexpected response data")

#pylint: disable=invalid-name
    def test_get_response_incorrect_id_type(self):
        """Test that an invalid id type request will return the inappropriate error."""
        with self.app.test_client() as client:
            response = client.get('/search/100W')
            self.assertEqual(response.status_code, 404, "Got unexpected status code")
            expected_response = ('{"reason": "404 Not Found: The requested URL was not found on '
                                 'the server.  If you entered the URL manually please check your '
                                 'spelling and try again."}')
            self.assertEqual(json.dumps(response.json), expected_response,
                             "Got unexpected response data")
#pylint: enable=invalid-name

    def test_get_response_empty_id(self):
        """Test that an invalid id type request will return the inappropriate error."""
        with self.app.test_client() as client:
            response = client.get('/search/')
            self.assertEqual(response.status_code, 404, "Got unexpected status code")
            expected_response = ('{"reason": "404 Not Found: The requested URL was not found on '
                                 'the server.  If you entered the URL manually please check your '
                                 'spelling and try again."}')
            self.assertEqual(json.dumps(response.json), expected_response,
                             "Got unexpected response data")

