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
from ..charts import chart_data
from .filters import ExpenseFilter
from .repository import ExpenseRepository
from .validation import validate_expense

bp = Blueprint("expenses", __name__, url_prefix="/expenses")


def _repo():
    return ExpenseRepository(get_db())


@bp.get("/")
def index():
    """The expenses page: filters, add form, list, total and charts."""
    expense_filter = ExpenseFilter.from_args(request.args)
    expenses = _repo().list(expense_filter)
    return render_template(
        "expenses/list.html",
        expenses=expenses,
        total=total(expenses),
        categories=CATEGORIES,
        chart_data=chart_data(expenses),
        # the page forms go back to; full_path ends with "?" when there is no filter
        next_url=request.full_path.rstrip("?"),
        today=date.today().isoformat(),
        **expense_filter.as_args(),
    )


@bp.route("/<int:expense_id>/edit", methods=["GET", "POST"])
def edit_expense(expense_id):
    repo = _repo()
    expense = repo.get(expense_id)
    if expense is None:
        abort(404)

    # where Cancel and Save go back to: the list the user came from
    next_url = request.values.get("next", "")
    if not is_safe_path(next_url):
        next_url = url_for("expenses.index")

    if request.method == "POST":
        try:
            updated = validate_expense(request.form)
        except ValidationError as error:
            # show the form again with what the user typed, so nothing is lost
            flash(str(error), "error")
            return render_template(
                "expenses/edit.html", expense=expense, form=request.form,
                categories=CATEGORIES, next_url=next_url,
            ), 400
        updated.id = expense_id
        repo.update(updated)
        flash("Expense updated.", "success")
        return redirect(next_url)

    return render_template(
        "expenses/edit.html", expense=expense, form=None,
        categories=CATEGORIES, next_url=next_url,
    )


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
