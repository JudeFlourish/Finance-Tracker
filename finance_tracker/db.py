"""SQLite connection handling. The only module that knows how to connect.

One connection is opened per request (stored on flask.g) and closed when the
request ends. Repositories get the connection passed in, they never open one.
"""
import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext


def connect(path):
    conn = sqlite3.connect(path)
    # rows can be read by column name, like row["amount"]
    conn.row_factory = sqlite3.Row
    return conn


def get_db():
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE"])
    return g.db


def close_db(exception=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db(conn):
    """Create the tables if they are missing. Safe to run more than once."""
    with current_app.open_resource("schema.sql") as f:
        conn.executescript(f.read().decode("utf-8"))
    conn.commit()


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Create the database tables."""
    init_db(get_db())
    click.echo("Database is ready.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    # create the tables on startup, so a fresh clone just works
    with app.app_context():
        init_db(get_db())
