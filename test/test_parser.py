"""Testing the database in a general sense and the parser specifically."""

from collections import namedtuple

from kaos.models import *
from kaos.parser import *

from . import KaosTestCase
from .context import kaos

OrbitPoint = namedtuple('OrbitPoint', 'time, pos, vel')

class TestEphemerisParser(KaosTestCase):
    """Ensures that the ephemeris parser behaves as expected."""

    def test_db_add_correct_num_rows(self):
        """Test that the add_segment_to_db adds the correct number of rows to the DB.  """
        sat = SatelliteInfo(platform_name="TEST")
        sat.save()
        DB.session.commit()

        orbit_data = []
        for i in range(0, 20):
            orbit_point = [float(j) for j in range(i, i+7)]
            orbit_tuple = OrbitPoint(orbit_point[0], orbit_point[1:4], orbit_point[4:7])
            orbit_data.append(orbit_tuple)

        add_segment_to_db(orbit_data, sat.platform_id)

        orbit_db = OrbitRecords()
        self.assertTrue(len(orbit_db.query.all()) == 20)

    def test_db_add_correct_orbit_data(self):
        """Test that the add_segment_to_db adds the correct row data to the DB. Validates time,
        position, and velocity for each DB row added."""
        sat = SatelliteInfo(platform_name="TEST")
        sat.save()
        DB.session.commit()

        orbit_data = []
        for i in range(0, 20):
            orbit_point = [float(j) for j in range(i, i+7)]
            orbit_tuple = OrbitPoint(orbit_point[0], orbit_point[1:4], orbit_point[4:7])
            orbit_data.append(orbit_tuple)

        add_segment_to_db(orbit_data, sat.platform_id)

        orbit_db = OrbitRecords()
        self.assertTrue(len(orbit_db.query.all()) == 20)

        orbits = orbit_db.query.all()
        for orbit_point, orbit in zip(orbit_data, orbits):
            self.assertTrue(orbit_point.time == orbit.time)
            self.assertTrue(orbit_point.pos == orbit.position)
            self.assertTrue(orbit_point.vel == orbit.velocity)

    def test_db_add_num_segments(self):
        """Test that the add_segment_to_db adds the correct number of "segments" to the db. Each
        call to add_segment_to_db should create only one segment at a time.  """

        # create and add first segment to DB
        sat = SatelliteInfo(platform_name="TEST1")
        sat.save()
        DB.session.commit()

        orbit_data = []
        for i in range(0, 20):
            orbit_point = [float(j) for j in range(i, i+7)]
            orbit_tuple = OrbitPoint(orbit_point[0], orbit_point[1:4], orbit_point[4:7])
            orbit_data.append(orbit_tuple)

        add_segment_to_db(orbit_data, sat.platform_id)

        orbit_segment = OrbitSegments()
        self.assertTrue(len(orbit_segment.query.all()) == 1)

        # create and add second segment
        sat2 = SatelliteInfo(platform_name="TEST2")
        sat2.save()
        DB.session.commit()

        orbit_data = []
        for i in range(40, 60):
            orbit_point = [float(j) for j in range(i, i+7)]
            orbit_tuple = OrbitPoint(orbit_point[0], orbit_point[1:4], orbit_point[4:7])
            orbit_data.append(orbit_tuple)

        add_segment_to_db(orbit_data, sat2.platform_id)

        # make sure we have two distincts segments in the DB
        self.assertTrue(len(orbit_segment.query.all()) == 2)

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

