"""Defines the base classes to be used in testing KAOS."""

import os, sys
from unittest import TestCase

sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('../kaos'))

import kaos
from kaos import create_app
from kaos.models import DB

class KaosTestCase(TestCase):
    """Test class that provides DB setup and teardown at the beginning and end of a test case."""

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


class KaosTestCaseNonPersistent(KaosTestCase):
    """Test classes subclassing this class will have the DB recreated in between each test."""
    
    def setUp(self):
        DB.create_all()

    def tearDown(self):
        DB.session.rollback()
        DB.session.commit()
        DB.drop_all()
