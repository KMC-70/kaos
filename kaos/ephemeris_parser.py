""""Handles the reading and parsing of ephemeris files.
Parsed files are stored in the DB.
"""

from kaos.models import DB, OrbitRecords, SatelliteInfo, OrbitSegments
from collections import namedtuple

class EphemerisParser(object):

    @staticmethod
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

        print("segment start: {}".format(segment_start))
        print("segment end: {}".format(segment_end))
        print("segment size: {}".format(len(segment)))

        """create segment entry.
        Retrieve segment ID and insert
        it along with data into Orbit db
        """
        segment_db = OrbitSegments("")
        segment_db.platform_id = satellite_id
        segment_db.start_time = segment_start
        segment_db.end_time = segment_end

        orbit_db = OrbitRecords("")
        for seg in segment:
            orbit_db.platform_id = satellite_id
            orbit_db.time = seg.time
            orbit_db.segment_id = segment_db.segment_id
            orbit_db.position = [seg.posx, seg.posy, seg.posz]
            orbit_db.velocity = [seg.velx, seg.vely, seg.velz]

        orbit_db.save()
        #DB.session.commit()

    @staticmethod
    def parse_file(file_handle, satellite_id):

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
                        orbital_row = namedtuple('orbit_point', 'time, posx, posy, posz, velx, vely, velz')
                        orbit_tuple = orbital_row._make(ephemeris_row)
                        segment_tuples.append(orbit_tuple)

                        """ The line we just read is a segment boundary,
                        So first check that this is the *end* of a segment and then
                        add this segment to the db.

                        A segment begins with the same time-stamp that the previous segment
                        ended with. So we don't want to commit the first entry in a
                        *new* segment. The last_seen_segment_boundary != orbit_tuple.time checks
                        this and makes sure not to commit to the db in this case.
                        """
                        if (orbit_tuple.time in segment_boundaries):
                            if (last_seen_segment_boundary != orbit_tuple.time):
                                last_seen_segment_boundary = orbit_tuple.time
                                EphemerisParser.add_segment_to_db(segment_tuples, satellite_id)
                                del segment_tuples[:]


                if "EphemerisTimePosVel" in line:
                    read_orbital_data = True



