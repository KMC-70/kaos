"""Interpolator for satellite position and velocity."""

import numpy as np
from scipy import interpolate

from kaos.models import OrbitSegment, OrbitRecord, Satellite
from ..errors import InterpolationError


class Interpolator:
    """Utility class to interpolate satellite position and velocity at arbitrary times,
    based on existing datapoints.
    """
    def __init__(self, platform_id):
        # check that the platform_id refers to a known satellite
        if not Satellite.get_by_id(platform_id):
            raise ValueError("platform_id does not exist: {}".format(platform_id))

        self.platform_id = platform_id
        self.segment_times = {}  # segment_id : list of times
        self.segment_positions = {}  # segment_id : list of positions
        self.segment_velocities = {}  # segment_id : list of velocities

    @staticmethod
    def vector_interp(times, vecs, new_times, kind):
        """Interpolate vectors for arbitrary timestamps, based on known timestamps.

        Args:
            times (array): A 1-D array containing timestamps of the input data.
            vecs (array): A numpy array containing the vector values to interpolate. Must be the
                same length as times.
            new_times (array): The times to interpolate for.
            kind: The type of interpolation to do. See scipy.interpolate for all options.

        Return:
            numpy array of interpolated points of the same length as targets, where ret[i]
            is the interpolated result for targets[i].
        """
        # interpolate position, then velocity
        approx = interpolate.interp1d(times, vecs, kind=kind, axis=0)
        return approx(np.array(new_times))

    @staticmethod
    def linear_interp(platform_id, timestamp):
        """Use linear interpolation to estimate the position and velocity of a satellite
        at a given time. For greater accuracy, use vector_interp() with kind="quadratic" or
        "cubic".

        Args:
            platform_id: The UID of the satellite.
            timestamp: The time for which to get the estimated position and velocity, in Unix
                epoch seconds.

        Return:
            A tuple (pos, vel). Both pos, vel are 3-tuples containing the vector components
            of the position and velocity. Return None if interpolation could not be done
            for the given satellite and timestamp.
        """
        # find the correct segment
        segment = OrbitSegment.get_by_platform_and_time(platform_id, timestamp)
        if not segment:
            raise InterpolationError("No segment found: {}, {}".format(platform_id, timestamp))

        orbit_records = OrbitRecord.get_by_segment(segment.segment_id)

        # can't do linear interpolation if we don't have enough records
        if not orbit_records or len(orbit_records) < 2:
            raise InterpolationError("Not enough records to perform interpolation: {}, {}".format(
                platform_id, timestamp))

        times = np.array([rec.time for rec in orbit_records])
        positions = np.array([np.array(rec.position) for rec in orbit_records])
        velocities = np.array([np.array(rec.velocity) for rec in orbit_records])

        # do the interpolation
        pos = Interpolator.vector_interp(times, positions, [timestamp], kind="linear")[0]
        vel = Interpolator.vector_interp(times, velocities, [timestamp], kind="linear")[0]

        return tuple(pos), tuple(vel)

    def interpolate(self, timestamp, kind="quadratic"):
        """Estimate the position and velocity of the satellite at a given time.

        Args:
            timestamp: The time for which to get the estimated position and velocity, in Unix
                epoch seconds.
            kind: The type of interpolation to do. This defaults to "quadratic." Alternatives
                include "linear", "cubic", etc. See scipy.interpolate.

        Return:
            A tuple (pos, vel). Each of pos, vel is a 3-tuple representing the vector
            components of the position and velocity, respectively.

        Raise:
            ValueError if interpolation could not be performed for the given timestamp.
        """
        # find the correct segment
        segment = OrbitSegment.get_by_platform_and_time(self.platform_id, timestamp)
        if not segment:
            raise InterpolationError("No segment found: {}, {}".format(self.platform_id, timestamp))

        # get orbit records for the segment
        segment_id = segment.segment_id
        if segment_id not in self.segment_times:
            records = OrbitRecord.get_by_segment(segment_id)

            # don't bother to proceed if there are too few records for an interpolation
            if not records or len(records) < 2:
                raise InterpolationError("No orbit records found: {}, {}".format(
                    self.platform_id, segment_id))

            # extract and cache time, position, velocity
            self.segment_times[segment_id] = np.array([rec.time for rec in records])
            self.segment_positions[segment_id] = np.array(
                [np.array(rec.position) for rec in records])
            self.segment_velocities[segment_id] = np.array(
                [np.array(rec.velocity) for rec in records])

        # interpolate the position and velocity
        position = Interpolator.vector_interp(self.segment_times[segment_id],
                                              self.segment_positions[segment_id],
                                              [timestamp], kind=kind)[0]
        velocity = Interpolator.vector_interp(self.segment_times[segment_id],
                                              self.segment_velocities[segment_id],
                                              [timestamp], kind=kind)[0]

        return tuple(position), tuple(velocity)
