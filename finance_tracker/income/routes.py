"""HTTP layer for income (US-04). No SQL and no validation rules in here.

Add models.py, validation.py and repository.py next to this file,
following the same shape as expenses/.
"""
from flask import Blueprint

bp = Blueprint("income", __name__, url_prefix="/income")
