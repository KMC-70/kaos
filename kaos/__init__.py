"""KAOS application initialization code."""

from __future__ import division, print_function

from flask import Flask, jsonify
from mpmath import mp

from kaos.api.errors import APIError


def create_app(config="settings.cfg"):
    """Create and setup the KAOS app."""

    # In order for visibility computations to be accurate a high degree of precision is required.
    # Hence, the mpmath library is configured to use 100 decimal point precision.
    mp.dps = 100

    # App configuration
    app = Flask(__name__)
    app.config.from_pyfile(config)

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

    return app
