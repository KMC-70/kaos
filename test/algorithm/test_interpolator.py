from kaos.models import DB, Satellite, OrbitSegment, OrbitRecord
from kaos.algorithm.interpolator import Interpolator

from .. import KaosTestCase

class TestInterpolator(KaosTestCase):
    @classmethod
    def setUpClass(cls):
        super(TestInterpolator, cls).setUpClass()

        # create a fake satellite
        cls.platform_id = 1
        satellite = Satellite(platform_id=cls.platform_id, platform_name="testsat")
        satellite.save()
        DB.session.commit()

        # add a segment for this satellite
        cls.segment_start = float(1)
        cls.segment_end = float(3)
        cls.segment = OrbitSegment(platform_id=cls.platform_id, 
                                   start_time=cls.segment_start, end_time=cls.segment_end)
        cls.segment.save()
        DB.session.commit()

        # create some segment data for the satellite
        for record in range(1, 4):
            t = float(record)
            orbit_record = OrbitRecord(segment_id=cls.segment.segment_id, 
                                       platform_id=cls.platform_id,
                                       time=t, position=(t, t, t), velocity=(t, t, t))
            orbit_record.save()

        DB.session.commit()

    def test_linear_interp__sucess(self):
        # test with a timestamp that is already in the database
        pos, vel = Interpolator.linear_interp(self.platform_id, 1.0)
        for component in pos:
            self.assertAlmostEqual(component, 1.0)
        for component in vel:
            self.assertAlmostEqual(component, 1.0)

        # test with a timestamp not already in the db
        # using simple linear interpolation, we should get 1.5 for all values
        pos, vel = Interpolator.linear_interp(self.platform_id, 1.5)
        for component in pos:
            self.assertAlmostEqual(component, 1.5)
        for component in vel:
            self.assertAlmostEqual(component, 1.5)

    def test_linear_interp__no_platform_id(self):
        with self.assertRaises(ValueError):
            result = Interpolator.linear_interp(1234, 1.0)

    def test_linear_interp__time_not_in_range(self):
        with self.assertRaises(ValueError):
            result = Interpolator.linear_interp(self.platform_id, 0.5)

    def test_linear_interp__too_few_data_points(self):
        # create a new segment for this satellite
        timestamp = self.segment_end + 1
        segment = OrbitSegment(platform_id=self.platform_id, start_time=timestamp,
                               end_time=timestamp)
        segment.save()
        DB.session.commit()

        # create a single record for this segment
        record = OrbitRecord(segment_id=segment.segment_id, platform_id=self.platform_id,
                             time=timestamp, position=(1.0, 1.0, 1.0),
                             velocity=(1.0, 1.0, 1.0))
        record.save()
        DB.session.commit()

        # linear interpolation should fail due to insufficent data points
        with self.assertRaises(ValueError):
            Interpolator.linear_interp(self.platform_id, timestamp=timestamp)

