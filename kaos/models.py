""""Describes the object representation of the tables in the database."""

from flask_sqlalchemy import SQLAlchemy
from flask_validator import ValidateInteger
from .validators import ValidateString

DB = SQLAlchemy()

class SavableModel(object):
    """SQL Alchemy model mixin used to enable quick saving."""

    def save(self):
        """Save but do not commit the current model."""
        DB.session.add(self)

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
        return '<Response History {}>'.format(self.uid)

    @classmethod
    def __declare_last__(cls):
        ValidateInteger(ResponseHistory.uid)
        ValidateString(ResponseHistory.response)

class SatelliteInfo(SavableModel, DB.Model):
    """This table holds all information about a specific satellite.

    The table holds the following information:
        platform_id:        Unique ID for the satellite
        platform_name:      The name of the satellite
        orbit_segments:     Time segments that the ephemeris records fall within
        orbit_records:      Satellite ephemeris records
        orbit_q_max:        The maximum distance from the earth center to the satellite position
    """
    __tablename__ = 'SatelliteInfo'

    platform_id = DB.Column(DB.Integer, primary_key=True)
    platform_name = DB.Column(DB.String(50), nullable=False)
    orbit_segments = DB.relationship("OrbitSegments", backref='satellite_info', lazy=True)
    orbit_records = DB.relationship("OrbitRecords", backref='satellite_info', lazy=True)
    orbit_q_max = DB.Column(DB.Float, nullable=True)


    @classmethod
    def __declare_last__(cls):
        ValidateInteger(SatelliteInfo.platform_id)
        ValidateString(SatelliteInfo.platform_name)

class OrbitSegments(SavableModel, DB.Model):
    """This table stores satellite ephemeris segment records which are collections of OrbitRecords
    in a given time period. These records are grouped together since some calculation must not use
    data that crosses segment boundaries.

    The table holds the following information:
        segment_id:     Unique ID for a particular time segment
        platform_id:    Unique ID for the satellite that owns this segment
        start_time:     Time in seconds since the Linux epoch that records in this segment start on
        end_time:       Time in seconds since the Linux epoch that records in this segment end on
        orbit_records:  Satellite ephemeris records that fall within the time segment and are owned
                        by the platform_id
    """
    __tablename__ = "OrbitSegments"

    segment_id = DB.Column(DB.Integer, primary_key=True)
    platform_id = DB.Column(DB.Integer, DB.ForeignKey('SatelliteInfo.platform_id'), nullable=False)
    start_time = DB.Column(DB.Float, nullable=False)
    end_time = DB.Column(DB.Float, nullable=False)
    orbit_records = DB.relationship("OrbitRecords", backref='orbit_segment', lazy=True)

    @classmethod
    def __declare_last__(cls):
        ValidateInteger(OrbitSegments.segment_id)
        ValidateInteger(OrbitSegments.platform_id)

class OrbitRecords(SavableModel, DB.Model):
    """This table stores satellite ephemeris records at specific points in time.

    The table holds the following information:
        uid:            Unique ID for a particular record
        platform__id    Unique ID for the satellite that owns this record
        segment_id:     Unique ID for the time segment that the orbit record falls within
        time            Time in seconds since the Linux epoch
        position        A 3 dimensional position vector whose units are defined by the satellite
        velocity        A 3 dimensional velocity vector whose units are defined by the satellite
    """
    __tablename__ = "OrbitRecords"

    uid = DB.Column(DB.Integer, primary_key=True)
    platform_id = DB.Column(DB.Integer, DB.ForeignKey('SatelliteInfo.platform_id'), nullable=False)
    segment_id = DB.Column(DB.Integer, DB.ForeignKey('OrbitSegments.segment_id'), nullable=False)
    time = DB.Column(DB.Float, nullable=False)
    position = DB.Column(DB.ARRAY(DB.Float), nullable=False)
    velocity = DB.Column(DB.ARRAY(DB.Float), nullable=False)

    @classmethod
    def __declare_last__(cls):
        ValidateInteger(OrbitRecords.uid)
