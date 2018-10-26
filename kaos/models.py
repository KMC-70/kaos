""""Describes the object representation of tables in the database."""

from flask_sqlalchemy import SQLAlchemy

DB = SQLAlchemy()

class ResponseHistory(DB.Model):
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

class SatelliteInfo(DB.Model):
    """This table holds all information about a specific satellite.

    The table holds the following information:
        uid:                Unique ID for the satellite
        name:               The name of the satellite
        timeposvel_records: Satellite ephemeris records
    """
    __tablename__ = 'SatelliteInfo'

    uid = DB.Column(DB.Integer, primary_key=True)
    name = DB.Column(DB.String(50), nullable=False)
    timeposvel_records = DB.relationship("TimePosVel", backref='satellite_info', lazy=True)

class SatelliteTimPosVel(DB.Model):
    """This table stores satellite ephemeris records at specific points in time.

    The table holds the following information:
        uid:            Unique ID for the particular record
        satellite_uid   Unique ID for the satellite that owns this record
        time            Time in seconds since the Linux epoch
        position        A 3 dimensional position vector whose units are defined by the satellite
        velocity        A 3 dimensional velocity vector whose units are defined by the satellite
    """
    __tablename__ = "SatelliteTimPosVel"

    uid = DB.Column(DB.Integer, primary_key=True)
    satellite_uid = DB.Column(DB.Integer, DB.ForeignKey('SatelliteInfo.uid'), nullable=False)
    time = DB.Column(DB.Integer, nullable=False)
    position = DB.Column(DB.ARRAY(DB.Integer, dimensions=3), nullable=False)
    velocity = DB.Column(DB.ARRAY(DB.Integer, dimensions=3), nullable=False)
