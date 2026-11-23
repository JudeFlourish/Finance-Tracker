"""HTTP layer for the home dashboard (US-04, US-05).

The dashboard only reads data through the other features' repositories,
it never writes SQL itself. Sums and progress go in a stats.py next to
this file, as plain functions that are easy to test.
"""
from flask import Blueprint, redirect, url_for

bp = Blueprint("dashboard", __name__)


@bp.get("/")
def home():
    # until the dashboard page is built, the home page shows the expenses
    return redirect(url_for("expenses.index"))
