"""
Initialization code for KAOS goes here.
"""

from flask import Flask

def create_app():
    """
    Create and setup the KAOS app.
    """
    app = Flask(__name__)

    # Setup code goes here.

    from kaos import api
    app.register_blueprint(api.bp)

    # pylint: disable=unused-variable,missing-docstring
    @app.route('/')
    def index():
        return 'Welcome to KAOS!'
    # pylint: enable=unused-variable,missing-docstring

    return app

