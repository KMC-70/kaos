from .context import kaos
from kaos import api, create_app

import pytest, unittest

def test_code_quality():
    """Pylint test."""
    from pylint import epylint as lint
    assert(not lint.py_run("kaos"))


class TestApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()

    def test_get_satellite_visibility(self):
        """
        Dummy unit test.
        """
        with self.app.test_client() as client:
            response = client.get('/api/')
            assert(response.data == "Bad API request, no satellites for you.")

