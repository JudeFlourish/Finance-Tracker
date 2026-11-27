"""SQLAlchemy set-up: the `db` object that every model uses.

The tables are defined by the models (expenses/models.py, income/models.py,
budgets/models.py). They are created and changed by the migrations in
migrations/versions/, run with `flask --app financeapp db upgrade`.
"""
import os

from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# every constraint gets a predictable name, e.g. "ck_expenses_amount_positive",
# so a migration can find it later to change or drop it
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    def to_dict(self):
        """The column values, e.g. {"id": 1, "amount": 12.5, ...}."""
        return {column.key: getattr(self, column.key) for column in self.__table__.columns}

    def __repr__(self):
        values = ", ".join(f"{key}={value!r}" for key, value in self.to_dict().items())
        return f"{type(self).__name__}({values})"


db = SQLAlchemy(model_class=Base)


# migrations/ sits next to the finance_tracker package; an absolute path so
# `flask db ...` works from any folder
MIGRATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "migrations")

# render_as_batch: SQLite can't change a column or constraint in place, so
# Alembic copies the table instead (needed when user_id is added in US-12)
migrate = Migrate(directory=MIGRATIONS_DIR, render_as_batch=True)


def import_models():
    """A model's table is only known to SQLAlchemy once its module is imported."""
    from .auth import models as _auth  # noqa: F401
    from .budgets import models as _budgets  # noqa: F401
    from .expenses import models as _expenses  # noqa: F401
    from .income import models as _income  # noqa: F401


def is_up_to_date():
    """True when every migration has been applied to the database."""
    config = Config()
    config.set_main_option("script_location", MIGRATIONS_DIR)
    latest = set(ScriptDirectory.from_config(config).get_heads())
    with db.engine.connect() as connection:
        applied = set(MigrationContext.configure(connection).get_current_heads())
    return applied == latest


def _warn_if_not_up_to_date(app):
    # checked once, on the first request, so `flask db upgrade` itself isn't warned
    checked = False

    @app.before_request
    def check_migrations():
        nonlocal checked
        if not checked:
            checked = True
            if not is_up_to_date():
                app.logger.warning(
                    "The database is not up to date. Run: uv run flask --app financeapp db upgrade"
                )


def init_app(app):
    # DATABASE is a file path (see config.py), SQLAlchemy wants it as a URL
    path = os.path.abspath(app.config["DATABASE"])
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", f"sqlite:///{path}")
    db.init_app(app)
    import_models()
    # adds the `flask db` commands (upgrade, migrate, downgrade, ...);
    # tables are created and changed by migrations/, not on startup
    migrate.init_app(app, db)
    if not app.testing:
        _warn_if_not_up_to_date(app)
