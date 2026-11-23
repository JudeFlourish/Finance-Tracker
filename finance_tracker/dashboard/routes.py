"""HTTP layer for the home dashboard (US-04, US-05).

The dashboard only reads data through the other features' repositories,
it never writes SQL itself. Sums and progress go in a stats.py next to
this file, as plain functions that are easy to test.

No url_prefix: the dashboard is meant to become the home page "/". That
page belongs to expenses for now, so moving it is part of the dashboard work.
"""
from flask import Blueprint

bp = Blueprint("dashboard", __name__)
