"""SQLAlchemy set-up: the `db` object that every model uses.

The tables are defined by the models (expenses/models.py, income/models.py,
budgets/models.py), not by hand-written SQL.
"""
import os

import click
from flask.cli import with_appcontext
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


def create_tables():
    """Create every table that is missing. Tables that already exist, and their
    data, are left alone, so this is safe to run on every start."""
    # a model's table is only known to SQLAlchemy once its module is imported
    from .budgets import models as _budgets  # noqa: F401
    from .expenses import models as _expenses  # noqa: F401
    from .income import models as _income  # noqa: F401

    db.create_all()


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Create the database tables."""
    create_tables()
    click.echo("Database is ready.")


def init_app(app):
    # DATABASE is a file path (see config.py), SQLAlchemy wants it as a URL
    path = os.path.abspath(app.config["DATABASE"])
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", f"sqlite:///{path}")
    db.init_app(app)
    app.cli.add_command(init_db_command)
    # create the tables on startup, so a fresh clone just works
    with app.app_context():
        create_tables()
