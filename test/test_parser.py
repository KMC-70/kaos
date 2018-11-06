"""Testing the database in a general sense and the models specifically."""

#from sqlalchemy.exc import IntegrityError, ProgrammingError

from . import KaosTestCase
#from .context import kaos
from kaos.ephemeris_parser import EphemerisParser


class TestEphemerisParser(KaosTestCase):
    """Ensures that the response history table behaves as expected."""

    def test_simple_parser1(self):
        """Test that an empty response cannot be commited to history."""
        ephem = EphemerisParser("/Users/jamieasefa/Documents/Courses/CPEN491/kaos/ephemeris/Radarsat2_J2000.e")
        EphemerisParser.parse_file("/Users/jamieasefa/Documents/Courses/CPEN491/kaos/ephemeris/Radarsat2_J2000.e", 1)

    def test_simple_parser2(self):
        """Test that an empty response cannot be commited to history."""
        ephem = EphemerisParser("/Users/jamieasefa/Documents/Courses/CPEN491/kaos/ephemeris/Radarsat2_Fixed.e")
        EphemerisParser.parse_file("/Users/jamieasefa/Documents/Courses/CPEN491/kaos/ephemeris/Radarsat2_Fixed.e", 1)
