"""Interpolator for satellite position and velocity."""

import numpy as np

from kaos.models import OrbitRecords, OrbitSegments

class Interpolator:
    """Utility class to interpolate satellite position and velocity at arbitrary times, 
    based on existing datapoints.
    """
    def __init__(self, platform_id):
        self.platform_id = platform_id

    @staticmethod
    def get_segment(platform_id, timestamp):
        """Get the orbit segment for the platform_id and time.

        Args:
            platform_id: The UID of the satellite.
            timestamp: The time to search for in Unix epoch seconds.

        Return:
            The orbit segment for this platform_id that contains the timestamp. If multiple
            segments include this timestamp, which may occur if timestamp is a segment
            boundary, then return the segment whose start time is timestamp. If no matching
            segment exists, return None.
        """
        # TODO move this to model
        # pylint: disable=undefined-variable
        return (OrbitSegments.query.filter(OrbitSegments.platform_id == platform_id,
                                           OrbitSegments.start_time <= timestamp,
                                           OrbitSegments.end_time >= timestamp)
                                    .order_by(OrbitSegments.start_time.desc())
                                    .first())
        # pylint: enable=undefined-variable

    @staticmethod
    def get_orbit_records_by_segment(segment_id):
        """Get all the orbit records in a segment.

        Args:
            segment_id: The segment id.

        Return:
            All the orbit records, sorted by time.
        """
        # TODO move this to model
        # pylint: disable=undefined-variable
        return (OrbitRecords.query.filter_by(segment_id=segment_id)
                                  .order_by(OrbitRecords.time)
                                  .all())
        # pylint: enable=undefined-variable
        
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
        segment = Interpolator.get_segment(platform_id, timestamp)
        if not segment:
            raise ValueError("No segment found: {}, {}".format(platform_id, timestamp))

        orbit_records = Interpolator.get_orbit_records_by_segment(segment.segment_id)

        # can't do linear interpolation in this case
        if not orbit_records or len(orbit_records) < 2:
            raise ValueError("Not enough records to perform interpolation: {}, {}".format(
                platform_id, timestamp))
        
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

