import numpy as np

from kaos.models import DB, Satellite, OrbitSegment, OrbitRecord
from kaos.algorithm.interpolator import Interpolator
from kaos.errors import InterpolationError

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
        cls.segment1 = OrbitSegment(platform_id=cls.platform_id, start_time=1., end_time=3.)
        cls.segment1.save()
        DB.session.commit()

        # simple segment data
        for record in range(1, 4):
            t = float(record)
            orbit_record = OrbitRecord(segment_id=cls.segment1.segment_id, 
                                       platform_id=cls.platform_id,
                                       time=t, position=(t, t, t), velocity=(t, t, t))
            orbit_record.save()

        # another segment
        cls.segment2 = OrbitSegment(platform_id=cls.platform_id, start_time=4., end_time=10.)
        cls.segment2.save()
        DB.session.commit()

        # more complex data this time
        times = np.arange(4, 11)
        positions = np.column_stack((np.sin(times), np.sin(times), np.sin(times)))
        velocities = np.column_stack(
                (np.exp(0.2 * times), np.exp(0.2 * times), np.exp(0.2 * times)))
        for i in range(times.size):
            orbit_record = OrbitRecord(segment_id=cls.segment2.segment_id,
                                       platform_id=cls.platform_id, time=times[i], 
                                       position=tuple(positions[i]), 
                                       velocity=tuple(velocities[i]))
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
        with self.assertRaises(InterpolationError):
            result = Interpolator.linear_interp(1234, 1.0)

    def test_linear_interp__time_not_in_range(self):
        with self.assertRaises(InterpolationError):
            result = Interpolator.linear_interp(self.platform_id, 0.5)

    def test_linear_interp__too_few_data_points(self):
        # create a new segment for this satellite
        timestamp = self.segment2.end_time + 1
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
        with self.assertRaises(InterpolationError):
            Interpolator.linear_interp(self.platform_id, timestamp=timestamp)

    def test_interpolate__success(self):
        interpolator = Interpolator(self.platform_id)

        # test a simple interpolation
        pos, vel = interpolator.interpolate(1.5)
        self.assertAlmostEqual(pos[0], 1.5)
        self.assertAlmostEqual(vel[0], 1.5)

        # test more complex interpolation
        for t in np.arange(self.segment2.start_time + 0.5, self.segment2.end_time, 1.):
            true_pos = np.sin(t)
            true_vel = np.exp(0.2 * t)

            pos, vel = interpolator.interpolate(t)
            self.assertAlmostEqual(pos[0], true_pos, delta=0.05)
            self.assertAlmostEqual(vel[0], true_vel, delta=0.05)
        
    def test_interpolate__no_platform_id(self):
        with self.assertRaises(ValueError):
            interpolator = Interpolator(self.platform_id+10)

    def test_interpolate__time_not_in_range(self):
        interpolator = Interpolator(self.platform_id)
        with self.assertRaises(InterpolationError):
            result = interpolator.interpolate(0.5)

    def test_interpolate__too_few_data_points(self):
        # create a new segment for this satellite
        timestamp = self.segment2.end_time + 10
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
        interpolator = Interpolator(self.platform_id)
        with self.assertRaises(InterpolationError):
            result = interpolator.interpolate(timestamp)
