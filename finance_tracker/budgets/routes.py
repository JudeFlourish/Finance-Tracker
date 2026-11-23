"""HTTP layer for budgets (US-05). No SQL and no validation rules in here."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from ..categories import CATEGORIES, COLORS
from ..db import get_db
from ..validation import ValidationError
from .repository import BudgetRepository
from .validation import validate_budget

bp = Blueprint("budgets", __name__, url_prefix="/budgets")


def _repo():
    return BudgetRepository(get_db())


@bp.get("/")
def list_budgets():
    # one row per category, with its budget or None, so any category can be set
    budgets = {b.category: b for b in _repo().list()}
    rows = [(category, budgets.get(category)) for category in CATEGORIES]
    return render_template("budgets/list.html", rows=rows, colors=COLORS)


@bp.post("/")
def save_budget():
    repo = _repo()
    try:
        budget = validate_budget(request.form)
    except ValidationError as error:
        flash(str(error), "error")
    else:
        changed = repo.get_by_category(budget.category) is not None
        repo.save(budget)
        action = "updated" if changed else "set"
        flash(f"{budget.category} budget {action} to ${budget.monthly_limit:.2f} a month.", "success")
    return redirect(url_for("budgets.list_budgets"))


@bp.post("/<int:budget_id>/delete")
def delete_budget(budget_id):
    # only the budget is removed, the category's expenses stay
    if not _repo().delete(budget_id):
        abort(404)
    flash("Budget removed.", "success")
    return redirect(url_for("budgets.list_budgets"))
