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

    numeric_level = getattr(logging, app.config['LOGGING_LEVEL'].upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: {}'.format(app.config['LOGGING_LEVEL'].upper()))

    # Create the logging directory if it doesnt exist
    if not os.path.isdir(app.config['LOGGING_DIRECTORY']):
        os.makedirs(app.config['LOGGING_DIRECTORY'])

    log_file_path = os.path.join(app.config['LOGGING_DIRECTORY'], app.config['LOGGING_FILE_NAME'])
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

    # Blueprint and view registration
    from kaos import api
    app.register_blueprint(api.history_bp)

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

