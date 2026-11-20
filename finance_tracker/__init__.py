"""Finance Tracker: a Flask app for tracking expenses.

The app is built by create_app() (the "application factory"), so tests can
make their own app with a temporary data file.
"""
from flask import Flask

from . import config


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(config.from_environment())
    if test_config:
        app.config.update(test_config)

    from .routes import bp
    app.register_blueprint(bp)
    return app
