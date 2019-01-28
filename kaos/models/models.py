"""Database models for KAOS."""

from flask_sqlalchemy import SQLAlchemy
from flask_validator import ValidateInteger
from sqlalchemy import Index

from .validators import ValidateString

DB = SQLAlchemy()

class SavableModel:
    """SQL Alchemy model mixin used to enable quick saving."""

    def save(self):
        """Save but do not commit the current model."""
        DB.session.add(self)


class Satellite(SavableModel, DB.Model):
    """This table holds all information about a specific satellite.

    The table holds the following information:
        platform_id:        Unique ID for the satellite
        platform_name:      The name of the satellite
        orbit_segments:     Time segments that the ephemeris records fall within
        orbit_records:      Satellite ephemeris records
        maximum_altitude:   The maximum distance from the earth center to the satellite position
    """
    __tablename__ = 'Satellite'

    platform_id = DB.Column(DB.Integer, primary_key=True)
    platform_name = DB.Column(DB.String(50), nullable=False)
    orbit_segments = DB.relationship("OrbitSegment", backref='satellite', lazy=True)
    orbit_records = DB.relationship("OrbitRecord", backref='satellite', lazy=True)
    maximum_altitude = DB.Column(DB.Float, nullable=True)

    def __repr__(self):
        return '<Satellite: platform_id={}, platform_name={}>'.format(self.platform_id,
                                                                      self.platform_name)

    @classmethod
    def __declare_last__(cls):
        ValidateInteger(Satellite.platform_id)
        ValidateString(Satellite.platform_name)

    @staticmethod
    def get_by_id(platform_id):
        """Get a satellite by its platform id.

        Args:
            platform_id: The unique ID for the satellite.

        Returns:
            The satellite, or None if no satellite with the given platform_id exists.
        """
        return Satellite.query.get(platform_id)

    @staticmethod
    def get_by_name(name):
        """Find a satellite by its name.

        Args:
            name: The satellite name.

        Returns:
            A list of satellites that match the name.
        """
        return Satellite.query.filter_by(platform_name=name).all()


class ResponseHistory(SavableModel, DB.Model):
    """This table serves as a generic cache to save the results of past requests so that they can be
    quickly retrieved in the future.
    """
    __tablename__ = 'ResponseHistory'

    uid = DB.Column(DB.Integer, primary_key=True)
    response = DB.Column(DB.String, nullable=False)

    def __init__(self, response):
        self.response = response

    def __repr__(self):
        return '<Response History: uid={}>'.format(self.uid)

    @classmethod
    def __declare_last__(cls):
        ValidateInteger(ResponseHistory.uid)
        ValidateString(ResponseHistory.response)

    @staticmethod
    def get_by_id(uid):
        """Find a response history entry by the UID assigned to the request when it was first made.

        Args:
            uid: The unique ID for the transaction.

        Returns:
            The ResponseHistory object, or None if not found.
        """
        return Satellite.query.get(uid)


class OrbitSegment(SavableModel, DB.Model):
    """This table stores satellite ephemeris segment records which are collections of OrbitRecords
    in a given time period. These records are grouped together since some calculations must not use
    data that crosses segment boundaries.

    The table holds the following information:
        segment_id:     Unique ID for a particular time segment
        platform_id:    Unique ID for the satellite that owns this segment
        start_time:     Time in seconds since the Linux epoch that records in this segment start on
        end_time:       Time in seconds since the Linux epoch that records in this segment end on
        orbit_records:  Satellite ephemeris records that fall within the time segment and are owned
                        by the platform_id
    """
    __tablename__ = "OrbitSegment"

    segment_id = DB.Column(DB.Integer, primary_key=True)
    platform_id = DB.Column(DB.Integer, DB.ForeignKey('Satellite.platform_id'), nullable=False)
    start_time = DB.Column(DB.Float, nullable=False)
    end_time = DB.Column(DB.Float, nullable=False)
    orbit_records = DB.relationship("OrbitRecord", backref='orbit_segment', lazy=True)

    # Add an index to improve query time for get_by_platform_and_time
    __table_args__ = (Index('OrbitSegment__platform_id__start_time', 'platform_id', 'start_time'), )

    @classmethod
    def __declare_last__(cls):
        ValidateInteger(OrbitSegment.segment_id)
        ValidateInteger(OrbitSegment.platform_id)

    @staticmethod
    def get_by_platform_and_time(platform_id, timestamp):
        """Find the segment that contains the given time, for the specified satellite.

        Args:
            platform_id: The unique ID of the satellite.
            timestamp: The time in seconds since the Unix epoch.

        Returns:
            The segment with a matching platform_id, and where start_time <= timestamp <= end_time.
            If more than one segment matches, which occurs only if the timestamp is the boundary
            of two segments, return the later segment. If no segment matches, return None.
        """
        # pylint: disable=undefined-variable
        return (OrbitSegment.query.filter(OrbitSegment.platform_id == platform_id,
                                          OrbitSegment.start_time <= timestamp,
                                          OrbitSegment.end_time >= timestamp)
                                  .order_by(OrbitSegment.start_time.desc())
                                  .first())
        # pylint: enable=undefined-variable


class OrbitRecord(SavableModel, DB.Model):
    """This table stores satellite ephemeris records at specific points in time.

    The table holds the following information:
        uid:            Unique ID for a particular record
        platform_id:    Unique ID for the satellite that owns this record
        segment_id:     Unique ID for the time segment that the orbit record falls within
        time:           Time in seconds since the Linux epoch
        position:       A 3 dimensional position vector whose units are defined by the satellite
        velocity:       A 3 dimensional velocity vector whose units are defined by the satellite
    """
    __tablename__ = "OrbitRecord"

    uid = DB.Column(DB.Integer, primary_key=True)
    platform_id = DB.Column(DB.Integer, DB.ForeignKey('Satellite.platform_id'),
                            nullable=False, index=True)
    segment_id = DB.Column(DB.Integer, DB.ForeignKey('OrbitSegment.segment_id'),
                           nullable=False, index=True)
    time = DB.Column(DB.Float, nullable=False, index=True)
    position = DB.Column(DB.ARRAY(DB.Float), nullable=False)
    velocity = DB.Column(DB.ARRAY(DB.Float), nullable=False)

    # Add an index to improve query time for get_by_platform_and_time
    __table_args__ = (Index('OrbitRecord__platform_id__time', 'platform_id', 'time'), )

    @classmethod
    def __declare_last__(cls):
        ValidateInteger(OrbitRecord.uid)

    @staticmethod
    def get_by_segment(segment_id):
        """Return all the records for a particular segment in ascending order by time.

        Args:
            segment_id (int): The unique ID for the segment.

        Returns:
            A list of all the OrbitRecords for that segment, or None if the segment doesn't exist.
        """
        return OrbitRecord.get_by_segments([segment_id]).get(segment_id)

    @staticmethod
    def get_by_segments(segment_ids):
        """Return all the records for a list of segment IDs.

        Args:
            segment_ids (list): A list of segment IDs.

        Returns: A dictionary where the key is a segment ID.
            {
                segment1: [record1, record2, ...],
                segment2: [record3, record4, ...],
                ...
            }
        """
        segments = {}
        for seg in segment_ids:
            segments[seg] = (OrbitRecord.query.filter_by(segment_id=seg)
                                              .order_by(OrbitRecord.time)
                                              .all())
        return segments

    @staticmethod
    def get_by_platform_and_time(platform_id, start_time, end_time):
        """Return all the records for a satellite, where start_time <= record time <= end_time.

        Args:
            platform_id (int): The unique ID for the satellite.
            start_time (int): The start time for the interval, in Unix epoch seconds.
            end_time (int): The end time for the interval, in Unix epoch seconds.

        Returns:
            A list of all the OrbitRecords that fit the supplied parameters, or None if there are
            no matching OrbitRecords.
        """
        return (OrbitRecord.query.filter(OrbitRecord.platform_id == platform_id,
                                         OrbitRecord.time >= start_time,
                                         OrbitRecord.time <= end_time)
                                 .order_by(OrbitRecord.time)
                                 .all())
