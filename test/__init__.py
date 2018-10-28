"""Defines the base classes to be used in testing KAOS."""

from flask_testing import TestCase

from .context import kaos
from kaos import create_app
from kaos.models import DB

class KaosTestCase(TestCase):
    """Test classes subclasing this class will have the DB recreaetd in between test cases."""

    def create_app(self):
        return create_app("settings_test.cfg")

    def setUp(self):
        DB.create_all()

    def tearDown(self):
        DB.session.remove()
        DB.drop_all()
