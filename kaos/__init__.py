"""KAOS application initialization code."""

from flask import Flask, jsonify

from kaos.api.errors import APIError


def create_app(config="settings.cfg"):
    """Create and setup the KAOS app."""

    # App configuration
    app = Flask(__name__)
    app.config.from_pyfile(config)

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

    return app
