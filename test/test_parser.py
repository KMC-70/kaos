"""Testing the database in a general sense and the models specifically."""

from sqlalchemy.exc import IntegrityError, ProgrammingError
from sqlalchemy.sql import operators

from . import KaosTestCase
from .context import kaos
from kaos.models import *
from kaos.parser import *

class TestEphemerisParser(KaosTestCase):
    """Ensures that the response history table behaves as expected."""

    def test_simple_parser_J2000(self):
        parse_ephemeris_file("ephemeris/Radarsat2_J2000.e")
        orbit = OrbitRecords()

        # test that the correct number of entries was created
        self.assertTrue(len(orbit.query.all()) == 17307) #taken from ephem file

    def test_simple_parser_Fixed(self):
        parse_ephemeris_file("ephemeris/Radarsat2_Fixed.e")
        orbit = OrbitRecords()

        # test that the correct number of entries was created
        self.assertTrue(len(orbit.query.all()) == 17307) #taken from ephem file
