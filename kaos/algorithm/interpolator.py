"""Interpolator for satellite position and velocity."""

import numpy as np

from kaos.models import OrbitSegment, OrbitRecord


class Interpolator:
    """Utility class to interpolate satellite position and velocity at arbitrary times,
    based on existing datapoints.
    """
    def __init__(self, platform_id):
        self.platform_id = platform_id

    @staticmethod
    def linear_interp(platform_id, timestamp):
        """Use linear interpolation to estimate the position and velocity of a satellite
        at a given time.

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
            raise ValueError("No segment found: {}, {}".format(platform_id, timestamp))

        orbit_records = OrbitRecord.get_by_segment(segment.segment_id)

        # can't do linear interpolation if we don't have enough records
        if not orbit_records or len(orbit_records) < 2:
            raise ValueError("Not enough records to perform interpolation: {}, {}".format(
                platform_id, timestamp))

        # pylint: disable=invalid-name
        xp = np.array([rec.time for rec in orbit_records])
        pos = np.array([np.array(rec.position) for rec in orbit_records])
        vel = np.array([np.array(rec.velocity) for rec in orbit_records])

        tpos = np.zeros(3)
        tvel = np.zeros(3)

        for i in range(3):
            tpos[i] = np.interp(x=timestamp, xp=xp, fp=pos[:, i])
            tvel[i] = np.interp(x=timestamp, xp=xp, fp=vel[:, i])

        return tuple(tpos), tuple(tvel)

    def interpolate(self, timestamp):
        """Estimate the position and velocity of the satellite at a given time.

        Args:
            timestamp: The time for which to get the estimated position and velocity, in Unix
                epoch seconds.

        Return:
            A tuple (pos, vel). Each of pos, vel is a 3-tuple representing the vector
            components of the position and velocity, respectively. If interpolation could
            not be done, return None.
        """
        return Interpolator.linear_interp(self.platform_id, timestamp)
