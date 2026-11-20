"""Finance Tracker: a Flask app for tracking expenses.

The app is built by create_app() (the "application factory"), so tests can
make their own app with a temporary database.
"""
import os

from flask import Flask

from . import config, db


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(config.from_environment(app.instance_path))
    if test_config:
        app.config.update(test_config)

    # make the folder for the SQLite file (instance/ by default, not committed)
    os.makedirs(os.path.dirname(os.path.abspath(app.config["DATABASE"])), exist_ok=True)
    db.init_app(app)

    from .routes import bp
    app.register_blueprint(bp)
    return app
