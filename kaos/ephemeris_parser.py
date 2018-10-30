""""Handles the reading and parsing of ephemeris files.
Parsed files are stored in the DB.
"""
import numpy as np
import .models
from collections import namedtuple

def parse_file(file_handle):
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


def add_segment_to_db(segment):
    segment_min = segment[0].time
    segment_max = segment[-1].time

