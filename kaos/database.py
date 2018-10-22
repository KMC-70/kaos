"""Handles connecting to the database as well as registering all the models."""

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from .settings import DATABASE_SETTINGS

ENGINE = create_engine('postgresql://{}:{}@{}:{}/{}'.format(DATABASE_SETTINGS['username'],
                                                            DATABASE_SETTINGS['password'],
                                                            DATABASE_SETTINGS['address'],
                                                            DATABASE_SETTINGS['port'],
                                                            DATABASE_SETTINGS['dbname']))
# This database object is thread safe, as guaranteed by SQL Alchemy
DB = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=ENGINE))

# SQL Alchemy supports multiple ways of interacting with the SQL database, the declarative method
# allows you to treat database tables as classes
# pylint: disable=invalid-name
Model = declarative_base()
Model.query = DB.query_property()
# pylint: enable=invalid-name

def init_db():
    """Create the database instance and binds all models to the database tables."""
    # pylint: disable=unused-variable
    from . import models
    Model.metadata.create_all(bind=ENGINE)
