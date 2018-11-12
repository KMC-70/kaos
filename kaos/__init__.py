"""KAOS application initialization code."""

from flask import Flask

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
    app.register_blueprint(api.bp)

    # pylint: disable=unused-variable,missing-docstring
    @app.route('/')
    def index():
        return 'Welcome to KAOS!'
    # pylint: enable=unused-variable,missing-docstring

    return app
