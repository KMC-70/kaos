"""Testing the database in a general sense and the parser specifically."""

from collections import namedtuple

from kaos.models import *
from kaos.parser import *

from . import KaosTestCase
from .context import kaos

OrbitPoint = namedtuple('OrbitPoint', 'time, pos, vel')

class TestEphemerisParser(KaosTestCase):
    """Ensures that the ephemeris parser behaves as expected."""

    def test_ephemeris_parser_single_file(self):
        """Light test to ensure that the parser can correctly parse an ephemeris file."""
        parse_ephemeris_file("ephemeris/Radarsat2_Fixed.e")

        # test that the correct number of entries was created
        self.assertTrue(len(OrbitRecords.query.all()) == 17307) #taken from ephem file

        self.assertTrue(len(OrbitSegments.query.all()) == 14) # taken from ephem file

        segment_boundaries = [0.0000000000000000e+00, 1.6340157216000001e+04,
                              4.7326755167999996e+04, 1.0207953590400000e+05,
                              1.8597513513600000e+05, 2.7627005577600002e+05,
                              3.6130918060800002e+05, 4.4658396489599999e+05,
                              5.3620515475200000e+05, 6.2089118179199996e+05,
                              6.8123706566399999e+05, 7.3718320319999999e+05,
                              8.5152938083199994e+05, 9.3618207907199999e+05,
                              1.0368000000000000e+06]

        seg_times = [float(seg) for seg in segment_boundaries]

        query = OrbitSegments.query.all()

        for segment, seg_start in zip(query, seg_times[:-1]):
            self.assertAlmostEqual(segment.start_time, seg_start)

        for segment, seg_end in zip(query, seg_times[1:]):
            self.assertAlmostEqual(segment.end_time, seg_end)

    def test_ephemeris_parser_multiple_file(self):
        parse_ephemeris_file("ephemeris/Radarsat2_Fixed.e")
        orbit = OrbitRecords()

        # test that the correct number of entries was created
        self.assertTrue(len(orbit.query.all()) == 17307) #taken from ephem file

        orbit_segment = OrbitSegments()

        self.assertTrue(len(orbit_segment.query.all()) == 14) # taken from ephem file

        parse_ephemeris_file("ephemeris/Radarsat2_J2000.e")
        orbit = OrbitRecords()

        # test that both files are included properly
        self.assertTrue(len(orbit.query.all()) == 34614)

        # segments from both files
        self.assertTrue(len(orbit_segment.query.all()) == 28)

