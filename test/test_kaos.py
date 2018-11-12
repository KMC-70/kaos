"""Sanity and API tests for KAOS"""

from .context import kaos
from kaos import api
from . import KaosTestCase

def test_code_quality():
    """Pylint test."""
    from pylint import epylint as lint
    assert not lint.py_run("kaos")


class TestApi(KaosTestCase):
    def test_get_satellite_visibility(self):
        """
        Dummy unit test.
        """
        with self.app.test_client() as client:
            response = client.get('/api/')
            self.assertTrue(response.data == "Bad API request, no satellites for you.")

