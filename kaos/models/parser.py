""""Handles the reading and parsing of ephemeris files. Parsed files are stored in the DB."""

import os

import numpy as np
from sqlalchemy import or_, and_

from kaos.utils.time_conversion import jdate_to_unix
from kaos.tuples import OrbitPoint
from kaos.models import DB, Satellite, OrbitSegment, OrbitRecord


def add_segment_to_db(orbit_data, satellite_id):
    """Add the given segment to the database.  We create a new entry in the Segment DB that holds i
    - segment_id
    - segment_start
    - segment_end
    - satellite_id

    This segment element is also used to index a group of rows in the Orbits DB. This lets us know
    that the orbit data belongs to a given segment. This is because we cannot perform interpolation
    using points in different segments.
    """

    if satellite_id < 0:
        return

    segment_start = orbit_data[0].time
    segment_end = orbit_data[-1].time

    # Abort if this segment overlaps with anything currently in the DB, because we cannot
    # interpolate across segments.
    if (OrbitSegment.query.filter(OrbitSegment.platform_id == satellite_id)
                          .filter(or_(and_((segment_start < OrbitSegment.start_time),
                                           (segment_end > OrbitSegment.start_time)),
                                      and_((segment_start < OrbitSegment.end_time),
                                           (segment_end > OrbitSegment.end_time)),
                                      and_((segment_start == OrbitSegment.start_time),
                                           (segment_end == OrbitSegment.end_time))))
                          .all()):
        return

    # Create segment entry. Retrieve segment ID and insert it along with data into Orbit db
    segment = OrbitSegment(platform_id=satellite_id, start_time=segment_start,
                           end_time=segment_end)
    segment.save()
    DB.session.commit()

    for orbit_point in orbit_data:
        orbit_record = OrbitRecord(platform_id=satellite_id, segment_id=segment.segment_id,
                                   time=orbit_point.time, position=orbit_point.pos,
                                   velocity=orbit_point.vel)
        orbit_record.save()

    DB.session.commit()


def parse_ephemeris_file(filename):
    """Parse the given ephemeris file and store the orbital data in OrbitRecords. We assume that
    each row in the ephemeris file is a 7-tuple containing an orbital point, formatted as:

    time posx posy posz velx vely velz

    Calculate the maximum distance from earth center to the position if the satellite. Insert it
    in Satellite.
    """
    sat = Satellite(platform_name=os.path.splitext(os.path.basename(filename))[0])
    sat.save()
    DB.session.commit()

    max_distance = 0

    with open(filename, "rU") as f:
        segment_boundaries = []
        segment_tuples = []
        start_time = float(0)

        read_segment_boundaries = False
        read_orbital_data = False

        # Remember the last seen segment boundary while reading the ephemeris rows. Needed to
        # differentiate between the beginning of a new segment and the end of en existing segment of
        # data
        last_seen_segment_boundary = 0

        for line in f:
            line = line.rstrip('\n')
            if "Epoch in JDate format:" in line:
                start_time = float(line.split(':')[1])
                start_time = jdate_to_unix(start_time)
                last_seen_segment_boundary = start_time

            # For now, we assume that the coord system will always be J2000
            # if "CoordinateSystem" in line:
            #     coord_system = str(line.split()[1])

            if "END SegmentBoundaryTimes" in line:
                read_segment_boundaries = False

            if read_segment_boundaries:
                line = line.strip()
                if line:
                    segment_boundaries.append(start_time + float(line))

            if "BEGIN SegmentBoundaryTimes" in line:
                read_segment_boundaries = True

            if "END Ephemeris" in line:
                add_segment_to_db(segment_tuples, sat.platform_id)
                read_orbital_data = False

            if read_orbital_data:
                line = line.strip()
                if line:
                    ephemeris_row = [float(num) for num in line.split()]
                    orbit_tuple = OrbitPoint(start_time + ephemeris_row[0], ephemeris_row[1:4],
                                             ephemeris_row[4:7])
                    segment_tuples.append(orbit_tuple)

                    # Keep track of the magnitude of the position vector and update with a bigger
                    # value
                    max_distance = max(max_distance, np.linalg.norm(ephemeris_row[1:4]))

                    # The line we just read is a segment boundary, So first check that this is the
                    # *end* of a segment, not the beginning of a new one, and then add this segment
                    # to the db.
                    if (orbit_tuple.time in segment_boundaries and
                            last_seen_segment_boundary != orbit_tuple.time):
                        last_seen_segment_boundary = orbit_tuple.time
                        add_segment_to_db(segment_tuples, sat.platform_id)
                        segment_tuples = []

            if "EphemerisTimePosVel" in line:
                read_orbital_data = True

            # After getting the q_max, insert it into Satellite"""
            sat.maximum_altitude = max_distance
            sat.save()
        DB.session.commit()
