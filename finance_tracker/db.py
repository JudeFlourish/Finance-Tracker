"""Plain sqlite3 connection for the repositories that still write their own SQL.

The tables themselves are created by SQLAlchemy (database.py). One connection
is opened per request (stored on flask.g) and closed when the request ends.
Repositories get the connection passed in, they never open one.
"""
import sqlite3

from flask import current_app, g


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
    # Flask calls this at the end of every request, also when it failed,
    # so a connection is never left open
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_app(app):
    app.teardown_appcontext(close_db)
