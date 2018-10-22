""""Describes the object representation of tables in the database."""

from sqlalchemy import Column, Integer, String

from .database import Model, DB

class ResponseHistory(Model):
    """This table serves as a generic cache to save the results of past requests so that they can be
    quickly retrieved in the future.
    """
    __tablename__ = 'ResponseHistory'

    uid = Column(Integer, primary_key=True)
    response = Column(String)

    def __init__(self, response):
        self.response = response

    def __repr__(self):
        return '<Response History {}>'.format(self.uid)

    def save(self):
        """Saves the current instance of object into the database."""
        DB.add(self)
