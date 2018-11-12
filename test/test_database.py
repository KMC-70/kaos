"""Testing the database in a general sense and the models specifically."""

from sqlalchemy.exc import IntegrityError, ProgrammingError

from . import KaosTestCaseNonPersistent
from .context import kaos
from kaos.models import *
from kaos.parser import *
from collections import namedtuple

OrbitPoint = namedtuple('OrbitPoint', 'time, pos, vel')

class TestResponseHistory(KaosTestCaseNonPersistent):
    """Ensures that the response history table behaves as expected."""

    def test_history_empty(self):
        """Test that an empty response cannot be commited to history."""
        response_history = ResponseHistory("")
        response_history.save()

        with self.assertRaises(ProgrammingError):
            DB.session.commit()

    def test_history_non_string(self):
        """Test that a non string response cannot be commited to history."""
        response_history = ResponseHistory(420)
        response_history.save()

        with self.assertRaises(ProgrammingError):
            DB.session.commit()

    def test_history_uid_non_int(self):
        """Test that a non int uid response cannot be commited to history."""
        response_history = ResponseHistory("WOW")
        response_history.uid = "Test"
        response_history.save()

        with self.assertRaises(ProgrammingError):
            DB.session.commit()

    def test_history_save_no_commit(self):
        """Test that non commited data is not saved to the database."""
        response_history = ResponseHistory("RESPONSE")
        response_history.save()

        DB.session.rollback()
        self.assertFalse(ResponseHistory.query.all())

    def test_history_save_commit(self):
        """Test that data is commited and saved to the database."""
        response_history = ResponseHistory("RESPONSE")
        response_history.save()
        DB.session.commit()

        DB.session.rollback()
        self.assertTrue(len(ResponseHistory.query.all()) == 1)
        self.assertTrue(ResponseHistory.query.all()[0].response == "RESPONSE")

    def test_history_save_arb_id(self):
        """Test that data is commited and saved to the database even if uid is assigned manually."""
        response_history = ResponseHistory("RESPONSE")
        response_history.uid = 420
        response_history.save()
        DB.session.commit()

        DB.session.rollback()
        self.assertTrue(len(ResponseHistory.query.all()) == 1)
        self.assertTrue(ResponseHistory.query.all()[0].response == "RESPONSE")
        self.assertTrue(ResponseHistory.query.all()[0].uid == 420)

    def test_history_save_same_id(self):
        """Test that we can't have two records with the same pk."""
        response_history_1 = ResponseHistory("RESPONSE_1")
        response_history_1.save()
        DB.session.commit()

        DB.session.rollback()
        self.assertTrue(len(ResponseHistory.query.all()) == 1)
        self.assertTrue(ResponseHistory.query.all()[0].response == "RESPONSE_1")

        response_history_2 = ResponseHistory("RESPONSE_2")
        response_history_2.uid = response_history_1.uid
        del response_history_1
        response_history_2.save()
        with self.assertRaises(IntegrityError):
            DB.session.commit()

    def test_single_segment_min_max(self):
        """Test that a single orbital segment has the correct
        start and end time."""
        sat = SatelliteInfo(platform_name="TEST")
        sat.save()
        DB.session.commit()

        start = 0.0
        end = 1000.0

        orbit_segment = OrbitSegments(platform_id=sat.platform_id, start_time=start,
                                        end_time=end)
        orbit_segment.save()
        DB.session.commit()

        query_min = orbit_segment.query.filter(orbit_segment.start_time == start).all()
        query_max = orbit_segment.query.filter(orbit_segment.end_time == end).all()

        for q_min, q_max in zip(query_min, query_max):
            self.assertTrue(q_min.start_time == start)
            self.assertTrue(q_max.end_time == end)

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
        self.assertTrue(len(OrbitRecords.query.all()) == 20)

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

        self.assertTrue(len(OrbitSegments.query.all()) == 1)

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
        self.assertTrue(len(OrbitSegments.query.all()) == 2)

    def test_duplicate_segments(self):
        """ Test that a duplicated segment for a satellite does not get added to the DB
        """
        sat = SatelliteInfo(platform_name="TEST")
        sat.save()
        DB.session.commit()

        orbit_data = []
        for i in range(0, 20):
            orbit_point = [float(j) for j in range(i, i+7)]
            orbit_tuple = OrbitPoint(orbit_point[0], orbit_point[1:4], orbit_point[4:7])
            orbit_data.append(orbit_tuple)

        add_segment_to_db(orbit_data, sat.platform_id)

        # try to add the same segment again
        orbit_data = []
        for i in range(0, 20):
            orbit_point = [float(j) for j in range(i, i+7)]
            orbit_tuple = OrbitPoint(orbit_point[0], orbit_point[1:4], orbit_point[4:7])
            orbit_data.append(orbit_tuple)

        add_segment_to_db(orbit_data, sat.platform_id)
        self.assertTrue(len(OrbitSegments.query.all()) == 1)


    def test_segment_overlapping_start_time(self):
        """ Test that a segment overlapping the start time of another segment does not
        get added to the DB.
        """
        sat = SatelliteInfo(platform_name="TEST")
        sat.save()
        DB.session.commit()

        orbit_data = []
        # time, posx, posy, posz, velx, vely, velz
        segment_start = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
        segment_end = [1.0, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
        orbit_tuple = OrbitPoint(segment_start[0], segment_start[1:4], segment_start[4:7])
        orbit_data.append(orbit_tuple)
        orbit_tuple = OrbitPoint(segment_end[0], segment_end[1:4], segment_end[4:7])
        orbit_data.append(orbit_tuple)

        add_segment_to_db(orbit_data, sat.platform_id)

        # try to add a segment overlapping the start time of the above segment
        orbit_data = []
        # time, posx, posy, posz, velx, vely, velz
        segment_start = [0.3, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
        segment_end = [0.7, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
        orbit_tuple = OrbitPoint(segment_start[0], segment_start[1:4], segment_start[4:7])
        orbit_data.append(orbit_tuple)
        orbit_tuple = OrbitPoint(segment_end[0], segment_end[1:4], segment_end[4:7])
        orbit_data.append(orbit_tuple)

        add_segment_to_db(orbit_data, sat.platform_id)
        self.assertTrue(len(OrbitSegments.query.all()) == 1)

    def test_segment_overlapping_end_time(self):
        """ Test that a segment overlapping the end time of another segment does not
        get added to the DB.
        """
        sat = SatelliteInfo(platform_name="TEST")
        sat.save()
        DB.session.commit()

        orbit_data = []
        # time, posx, posy, posz, velx, vely, velz
        segment_start = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
        segment_end = [1.0, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
        orbit_tuple = OrbitPoint(segment_start[0], segment_start[1:4], segment_start[4:7])
        orbit_data.append(orbit_tuple)
        orbit_tuple = OrbitPoint(segment_end[0], segment_end[1:4], segment_end[4:7])
        orbit_data.append(orbit_tuple)

        add_segment_to_db(orbit_data, sat.platform_id)

        # try to add a segment overlapping the start time of the above segment
        orbit_data = []
        # time, posx, posy, posz, velx, vely, velz
        segment_start = [0.7, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
        segment_end = [1.2, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
        orbit_tuple = OrbitPoint(segment_start[0], segment_start[1:4], segment_start[4:7])
        orbit_data.append(orbit_tuple)
        orbit_tuple = OrbitPoint(segment_end[0], segment_end[1:4], segment_end[4:7])
        orbit_data.append(orbit_tuple)

        add_segment_to_db(orbit_data, sat.platform_id)
        self.assertTrue(len(OrbitSegments.query.all()) == 1)

    def test_overlapping_entire_segment(self):
        """ Test that a segment overlapping the entire time period of the segment does not
        get added to the DB.
        """
        sat = SatelliteInfo(platform_name="TEST")
        sat.save()
        DB.session.commit()

        orbit_data = []
        # time, posx, posy, posz, velx, vely, velz
        segment_start = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
        segment_end = [1.0, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
        orbit_tuple = OrbitPoint(segment_start[0], segment_start[1:4], segment_start[4:7])
        orbit_data.append(orbit_tuple)
        orbit_tuple = OrbitPoint(segment_end[0], segment_end[1:4], segment_end[4:7])
        orbit_data.append(orbit_tuple)

        add_segment_to_db(orbit_data, sat.platform_id)

        # try to add a segment overlapping the start time of the above segment
        orbit_data = []
        # time, posx, posy, posz, velx, vely, velz
        segment_start = [0.3, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
        segment_end = [1.2, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
        orbit_tuple = OrbitPoint(segment_start[0], segment_start[1:4], segment_start[4:7])
        orbit_data.append(orbit_tuple)
        orbit_tuple = OrbitPoint(segment_end[0], segment_end[1:4], segment_end[4:7])
        orbit_data.append(orbit_tuple)

        add_segment_to_db(orbit_data, sat.platform_id)
        self.assertTrue(len(OrbitSegments.query.all()) == 1)
