"""HTTP layer for expenses. No SQL and no validation rules in here."""
import csv
import io
from datetime import date

from flask import Blueprint, Response, abort, flash, redirect, render_template, request, url_for

from ..categories import CATEGORIES
from ..db import get_db
from ..models import total
from ..validation import ValidationError
from ..web import is_safe_path, redirect_back
from .charts import chart_data
from .filters import ExpenseFilter
from .repository import ExpenseRepository
from .validation import validate_expense

bp = Blueprint("expenses", __name__, url_prefix="/expenses")


def _repo():
    return ExpenseRepository(get_db())


def _render_page(next_url, edit_expense=None):
    """The expenses page: filters, add or edit form, list, total and charts.

    next_url is the list page (with its filter) that forms go back to.
    """
    expense_filter = ExpenseFilter.from_args(request.args)
    expenses = _repo().list(expense_filter)
    return render_template(
        "expenses/list.html",
        expenses=expenses,
        total=total(expenses),
        categories=CATEGORIES,
        chart_data=chart_data(expenses),
        edit_expense=edit_expense,
        next_url=next_url,
        today=date.today().isoformat(),
        **expense_filter.as_args(),
    )


@bp.get("/")
def index():
    # full_path ends with "?" when there is no filter, e.g. "/expenses/?"
    return _render_page(next_url=request.full_path.rstrip("?"))


@bp.get("/edit/<int:expense_id>")
def edit_expense(expense_id):
    expense = _repo().get(expense_id)
    if expense is None:
        abort(404)
    next_url = request.args.get("next", "")
    if not is_safe_path(next_url):
        next_url = url_for("expenses.index")
    return _render_page(next_url=next_url, edit_expense=expense)


@bp.post("/update/<int:expense_id>")
def update_expense(expense_id):
    repo = _repo()
    # check the id before the form, so an unknown id is always a 404
    # and never sends the user to an edit page that doesn't exist
    if repo.get(expense_id) is None:
        abort(404)
    try:
        expense = validate_expense(request.form)
    except ValidationError as error:
        # back to the edit form, still remembering where to go after saving
        flash(str(error), "error")
        return redirect(url_for("expenses.edit_expense", expense_id=expense_id,
                                next=request.form.get("next", "")))
    expense.id = expense_id
    repo.update(expense)
    flash("Expense updated.", "success")
    return redirect_back("expenses.index")


@bp.post("/add")
def add_expense():
    try:
        expense = validate_expense(request.form)
    except ValidationError as error:
        flash(str(error), "error")
    else:
        _repo().add(expense)
        flash("Expense added.", "success")
    return redirect_back("expenses.index")


@bp.post("/delete/<int:expense_id>")
def delete_expense(expense_id):
    if not _repo().delete(expense_id):
        abort(404)
    flash("Expense deleted.", "success")
    return redirect_back("expenses.index")


@bp.get("/export")
def export_csv():
    # exports only what you see with the current filter, oldest first
    expenses = _repo().list(ExpenseFilter.from_args(request.args), newest_first=False)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Description", "Category", "Amount"])
    for e in expenses:
        writer.writerow([e.date, e.description, e.category, f"{e.amount:.2f}"])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=expenses.csv"},
    )
