""""Handles the reading and parsing of ephemeris files.
Parsed files are stored in the DB.
"""

from collections import namedtuple

from kaos.models import DB, OrbitRecords, SatelliteInfo, OrbitSegments
from .algorithm import Vector3D

OrbitPoint = namedtuple('OrbitPoint', 'time, pos, vel')

class EphemerisParser(object):

    @staticmethod
    def add_segment_to_db(orbit_data, satellite_id):
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
        # TODO Validate satellite_id 

        segment_start = orbit_data[0].time
        segment_end = orbit_data[-1].time

        print("segment start: {}".format(segment_start))
        print("segment end: {}".format(segment_end))

        """create segment entry.
        Retrieve segment ID and insert
        it along with data into Orbit db
        """
        # TODO Check if a segment exists that overlaps this segment


        segment = OrbitSegments(platform_id=satellite_id, start_time=int(segment_start),
                                end_time=int(segment_end))
        segment.save()
        DB.session.commit()

        for orbit_point in orbit_data:
            # TODO Validate uniqueness for this platform
            orbit_record = OrbitRecords(platform_id=satellite_id, segment_id=segment.segment_id,
                                        time=orbit_point.time, position=orbit_point.pos,
                                        velocity=orbit_point.vel)
            orbit_record.save()

        DB.session.commit()

    @staticmethod
    def parse_file(file_handle, satellite_id):

        # TODO Create the satelite if not present
        # Look at test

        with open(file_handle, "rU") as f:
            """A list containing each of the 15 or so
            segment boundaries outlined in the SegmentBoundaryTimes
            portion of the ephemeris file"""
            segment_boundaries = []

            """A list containing the orbit data rows
            within a segment"""
            segment_tuples = []

            """Flags"""
            read_segment_boundaries = False
            read_orbital_data = False

            """Remembers the last seen segment boundary
            while reading the ephemeris rows. Needed
            to differentiate between the beginning
            of a new segment and the end of en existing
            segment of data"""
            last_seen_segment_boundary = 0

            for line in f:
                line = line.rstrip('\n')
                if "Epoch in JDate format:" in line:
                    start_time = float(line.split(':')[1])

                if "CoordinateSystem" in line:
                    coord_system = str(line.split()[1])

                if "END SegmentBoundaryTimes" in line:
                    read_segment_boundaries = False

                if (read_segment_boundaries):
                    line = line.strip()
                    if line:
                        segment_boundaries.append(float(line))

                if "BEGIN SegmentBoundaryTimes" in line:
                    read_segment_boundaries = True

                if "END Ephemeris" in line:
                    read_orbital_data = False

                if (read_orbital_data):
                    line = line.strip()
                    if line:
                        """each row is a 7-tuple formatted as
                        time posx posy posz velx vely velz"""
                        ephemeris_row = [float(num) for num in line.split()]
                        orbit_tuple = OrbitPoint(ephemeris_row[0], ephemeris_row[1:4],
                                                 ephemeris_row[4:7])
                        segment_tuples.append(orbit_tuple)

                        """ The line we just read is a segment boundary,
                        So first check that this is the *end* of a segment and then
                        add this segment to the db.

                        A segment begins with the same time-stamp that the previous segment
                        ended with. So we don't want to commit the first entry in a
                        *new* segment. The last_seen_segment_boundary != orbit_tuple.time checks
                        this and makes sure not to commit to the db in this case.
                        """
                        if orbit_tuple.time in segment_boundaries:
                            if last_seen_segment_boundary != orbit_tuple.time:
                                last_seen_segment_boundary = orbit_tuple.time
                                EphemerisParser.add_segment_to_db(segment_tuples, satellite_id)
                                del segment_tuples[:]


                if "EphemerisTimePosVel" in line:
                    read_orbital_data = True

            DB.session.commit()

