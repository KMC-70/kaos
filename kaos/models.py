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
        timeposvel_records: Satellite ephemeris records
    """
    __tablename__ = 'SatelliteInfo'

    platform_id = DB.Column(DB.Integer, primary_key=True)
    platform_name = DB.Column(DB.String(50), nullable=False)
    orbit_records = DB.relationship("OrbitRecords", backref='satellite_info', lazy=True)

    @classmethod
    def __declare_last__(cls):
        ValidateInteger(SatelliteInfo.platform_id)
        ValidateString(SatelliteInfo.platform_name)

class OrbitRecords(SavableModel, DB.Model):
    """This table stores satellite ephemeris records at specific points in time.

    The table holds the following information:
        uid:            Unique ID for a particular record
        platform__id    Unique ID for the satellite that owns this record
        time            Time in seconds since the Linux epoch
        position        A 3 dimensional position vector whose units are defined by the satellite
        velocity        A 3 dimensional velocity vector whose units are defined by the satellite
    """
    __tablename__ = "OrbitRecords"

    uid = DB.Column(DB.Integer, primary_key=True)
    platform_id = DB.Column(DB.Integer, DB.ForeignKey('SatelliteInfo.platform_id'), nullable=False)
    time = DB.Column(DB.Integer, nullable=False)
    position = DB.Column(DB.ARRAY(DB.Float, dimensions=3), nullable=False)
    velocity = DB.Column(DB.ARRAY(DB.Float, dimensions=3), nullable=False)

    @classmethod
    def __declare_last__(cls):
        ValidateInteger(OrbitRecords.uid)
        ValidateInteger(OrbitRecords.time)
