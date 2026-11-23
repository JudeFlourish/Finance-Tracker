"""HTTP layer for income (US-04). No SQL and no validation rules in here."""
from datetime import date

from flask import Blueprint, abort, flash, render_template, request

from ..db import get_db
from ..models import total
from ..validation import ValidationError
from ..web import redirect_back
from .repository import IncomeRepository
from .validation import validate_income

bp = Blueprint("income", __name__, url_prefix="/income")


def _repo():
    return IncomeRepository(get_db())


@bp.get("/")
def list_income():
    income = _repo().list()
    return render_template(
        "income/list.html",
        income=income,
        total=total(income),
        today=date.today().isoformat(),
        next_url=request.full_path.rstrip("?"),
    )


# the forms send a hidden "next" field, so a form on another page
# (like the dashboard's quick add) goes back to that page afterwards
@bp.post("/")
def add_income():
    try:
        income = validate_income(request.form)
    except ValidationError as error:
        flash(str(error), "error")
    else:
        _repo().add(income)
        flash("Income added.", "success")
    return redirect_back("income.list_income")


@bp.post("/<int:income_id>/delete")
def delete_income(income_id):
    if not _repo().delete(income_id):
        abort(404)
    flash("Income deleted.", "success")
    return redirect_back("income.list_income")
