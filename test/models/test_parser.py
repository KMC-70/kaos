"""Testing the database in a general sense and the parser specifically."""

import numpy as np

from kaos.models import DB, Satellite, ResponseHistory, OrbitSegment, OrbitRecord
from kaos.models.parser import *

from .. import KaosTestCaseNonPersistent

class TestEphemerisParser(KaosTestCaseNonPersistent):
    """Ensures that the ephemeris parser behaves as expected."""

    def test_ephemeris_parser_single_file(self):
        """Light test to ensure that the parser can correctly parse an ephemeris file."""
        parse_ephemeris_file("ephemeris/Radarsat2.e")

        # test that the correct number of entries was created
        self.assertTrue(len(OrbitRecord.query.all()) == 17307) #taken from ephem file

        self.assertTrue(len(OrbitSegment.query.all()) == 14) # taken from ephem file

        # epoch start in JDate format
        jdate_start = jdate_to_unix(2458119.50000000000000)

        segment_boundaries = [0.0000000000000000e+00, 1.6340157216000001e+04,
                              4.7326755167999996e+04, 1.0207953590400000e+05,
                              1.8597513513600000e+05, 2.7627005577600002e+05,
                              3.6130918060800002e+05, 4.4658396489599999e+05,
                              5.3620515475200000e+05, 6.2089118179199996e+05,
                              6.8123706566399999e+05, 7.3718320319999999e+05,
                              8.5152938083199994e+05, 9.3618207907199999e+05,
                              1.0368000000000000e+06]

        seg_times = [jdate_start + float(seg) for seg in segment_boundaries]

        query = OrbitSegment.query.all()

        for segment, seg_start in zip(query, seg_times[:-1]):
            self.assertAlmostEqual(segment.start_time, seg_start, places=4)

        for segment, seg_end in zip(query, seg_times[1:]):
            self.assertAlmostEqual(segment.end_time, seg_end, places=4)

    def test_ephemeris_parser_multiple_file(self):
        parse_ephemeris_file("ephemeris/Radarsat2.e")
        orbit = OrbitRecord()

        # test that the correct number of entries was created
        self.assertTrue(len(orbit.query.all()) == 17307) #taken from ephem file

        orbit_segment = OrbitSegment()

        self.assertTrue(len(orbit_segment.query.all()) == 14) # taken from ephem file

        parse_ephemeris_file("ephemeris/Radarsat2.e")
        orbit = OrbitRecord()

        # test that both files are included properly
        self.assertTrue(len(orbit.query.all()) == 34614)

        # segments from both files
        self.assertTrue(len(orbit_segment.query.all()) == 28)

    def test_find_maximum_distance(self):
        largest_q = 0
        parse_ephemeris_file("ephemeris/Radarsat2.e")
        with open("ephemeris/Radarsat2.e") as file:
            for num, line in enumerate(file,1):
                line = line.rstrip('\n')
                if num > 46 and num < 17366:
                    position_row = [float(num) for num in line.split()]
                    largest_q = max(largest_q, np.linalg.norm(position_row[1:4]))
        temp = Satellite.query.filter_by(platform_id=1).first().maximum_altitude
        self.assertAlmostEqual(temp, largest_q)



