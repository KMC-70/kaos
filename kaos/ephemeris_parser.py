""""Handles the reading and parsing of ephemeris files.
Parsed files are stored in the DB.
"""
import numpy as np
from .context import kaos
from kaos.models import DB, OrbitRecords, SatelliteInfo
from collections import namedtuple

def parse_file(file_handle, satellite_id):
    orbital_data = []
    segment_boundaries = []
    with open(file_handle, "rU") as f:
        segment_tuples = []
        for line in f:
            line = line.rstrip('\n')
            if "Epoch in JDate format:" in line:
                start_time = float(line.split(':')[1])

            if "CoordinateSystem" in line:
                coord_system = str(line.split()[1])

            if "BEGIN SegmentBoundaryTimes" in line:
                read_segment_boundaries = True

            if "END SegmentBoundaryTimes" in line:
                read_segment_boundaries = False

            if (read_segment_boundaries):
                line = line.strip()
                if line:
                    segment_boundaries.insert(format(line, 'f'))

            if "EphemerisTimePosVel" in line:
                read_orbital_data = True

            if "END Ephemeris" in line:
                read_orbital_data = False

            if (read_orbital_data):
                if line:
                    """each row is a 7-tuple formatted as
                    time posx posy posz velx vely velz"""
                    ephemeris_row = [format(num, 'f') for num in line.split()]
                    orbital_row = namedtuple('orbit_point', 'time, posx, posy, posz, velx, vely, velz')
                    orbit_tuple = orbital_row._make(ephemeris_row)
                    segment_tuples.insert(orbit_tuple)

                    """ The line we just read is a segment boundary,
                    So add this segment to the db
                    """
                    if (orbit_tuple.time in segment_boundaries):
                        add_segment_to_db(segment_tuples, satellite_id)
                        segment_tuples.clear()


def add_segment_to_db(segment, satellite_id):
    """Add the given segment to the database.
    We create a new entry in the Segment DB that holds
    - segment_id
    - segment_start
    - segment_end
    - satellite_id

    This segment element is also used to index a group of
    rows in the Orbits DB. This lets us know that the orbit
    data belongs to a given segment. This is because
    we cannot perform interpolation using points in
    different segments.
    """
    segment_start = segment[0].time
    segment_end = segment[-1].time

    """create segment entry.
    Retrieve segment ID and insert
    it along with data into Orbit db
    """

    orbit_db = OrbitRecords.get_db()
    for seg in segment:
        orbit_db.platform_id = satellite_id



    orbit_db.save()

    #DB.session.commit()

