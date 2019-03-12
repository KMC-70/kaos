"""KAOS application initialization code."""

from __future__ import division

import atexit
import logging
import sys
import os
import os.path
from time import gmtime, strftime

from flask import Flask, jsonify
from mpmath import mp

from kaos.api.errors import APIError


def create_app(config="settings.cfg"):
    """Create and setup the KAOS app."""

    # App configuration
    app = Flask(__name__)
    app.config.from_pyfile(config)

    # In order for visibility computations to be accurate a high degree of precision is required.
    # Hence, the mpmath library is configured to use 100 decimal point precision.
    mp.dps = app.config.get('CALCULATION_PRECISION', 100)

    # Configure Logging
    logging_level = app.config.get('LOGGING_LEVEL', 'INFO').upper()
    logging_directory = app.config.get('LOGGING_DIRECTORY', '.')
    logging_file = app.config['LOGGING_FILE_NAME']

    numeric_level = getattr(logging, logging_level, None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: {}'.format(logging_level))

    # Create the logging directory if it doesn't exist
    if not os.path.isdir(logging_directory):
        os.makedirs(logging_directory)

    log_file_path = os.path.join(logging_directory, logging_file)
    logging.basicConfig(filename=strftime(log_file_path, gmtime()),
                        format='%(asctime)s %(levelname)s %(module)s %(message)s',
                        level=numeric_level)

    # Python 2 does not support initializing both the stream and file handler for logging.
    # Therefore, the stream handler must be initialized separately.
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(logging.getLogger().handlers[0].formatter)
    logging.getLogger().addHandler(console_handler)

    # Database setup
    from kaos.models import DB
    DB.init_app(app)
    DB.create_all(app=app)

    # Cache setup
    from kaos.models.models import CACHE
    CACHE.init_app(app)

    # Blueprint and view registration
    from kaos import api
    app.register_blueprint(api.history_bp)
    app.register_blueprint(api.visibility_bp)
    app.register_blueprint(api.opertunity_bp)

    # pylint: disable=unused-variable,missing-docstring
    @app.route('/')
    def index():
        return 'Welcome to KAOS!'

    # Setup default error handlers. 404 and 505 are special case handlers because the framework can
    # throw them automatically.
    @app.errorhandler(405)
    @app.errorhandler(404)
    def method_not_allowed(error):
        response = jsonify(reason=str(error))
        response.status_code = error.code
        return response

    @app.errorhandler(APIError)
    def api_error(error):
        return error.to_response()
    # pylint: enable=unused-variable,missing-docstring

    logging.info('======= KAOS START =======')

    return app


def application_exit():
    """KAOS exit handler."""
    logging.info("======= KAOS SHUTDOWN =======")


atexit.register(application_exit)
