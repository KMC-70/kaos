"""KAOS application initialization code."""

from flask import Flask

from . import database

def create_app():
    """Create and setup the KAOS app."""
    app = Flask(__name__)
    # Setup code goes here.

    database.init_db()
    from kaos import api
    app.register_blueprint(api.bp)

    # pylint: disable=unused-variable,missing-docstring,unused-argument
    @app.route('/')
    def index():
        return 'Welcome to KAOS!'

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        database.DB.remove()
    # pylint: enable=unused-variable,missing-docstring,unused-argument

    return app
