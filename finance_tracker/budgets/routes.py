"""HTTP layer for budgets (US-05). No SQL and no validation rules in here.

Add models.py, validation.py and repository.py next to this file,
following the same shape as expenses/.
"""
from flask import Blueprint

bp = Blueprint("budgets", __name__, url_prefix="/budgets")
