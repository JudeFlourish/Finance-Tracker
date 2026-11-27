"""Finance Tracker: a Flask app for tracking expenses.

The app is built by create_app() (the "application factory"), so tests can
make their own app with a temporary database.
"""
import os

from flask import Flask

from . import config, database, importer, web


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(config.from_environment(app.instance_path))
    if test_config:
        app.config.update(test_config)

    # make the folder for the SQLite file (instance/ by default, not committed)
    os.makedirs(os.path.dirname(os.path.abspath(app.config["DATABASE"])), exist_ok=True)
    database.init_app(app)
    importer.init_app(app)
    web.init_app(app)

    _register_blueprints(app)
    return app


def _register_blueprints(app):
    # each feature is its own blueprint, adding a feature = one line here
    from .budgets.routes import bp as budgets_bp
    from .dashboard.routes import bp as dashboard_bp
    from .expenses.routes import bp as expenses_bp
    from .income.routes import bp as income_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(income_bp)
    app.register_blueprint(budgets_bp)
