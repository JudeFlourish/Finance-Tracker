"""Home dashboard: one month at a glance (US-04, US-05).

Only reads, through the other features' repositories. It never queries the database itself;
the quick-add forms post to the expenses and income pages, which send the
user back here with the hidden "next" field.
"""
from datetime import date

from flask import Blueprint, render_template, request

from ..budgets.repository import BudgetRepository
from ..categories import CATEGORIES, COLORS
from ..charts import chart_data
from ..database import db
from ..expenses.filters import ExpenseFilter
from ..expenses.repository import ExpenseRepository
from ..income.repository import IncomeRepository
from ..models import total
from . import stats

bp = Blueprint("dashboard", __name__)


@bp.get("/")
def home():
    today = date.today()
    month = stats.parse_month(request.args.get("month"), today)

    expenses = ExpenseRepository(db.session).list(ExpenseFilter(start=month.start, end=month.end))
    income = IncomeRepository(db.session).list(start=month.start, end=month.end)
    budgets = BudgetRepository(db.session).list()

    spent = total(expenses)
    earned = total(income)
    return render_template(
        "dashboard/home.html",
        month=month,
        is_current_month=month.contains(today.isoformat()),
        earned=earned,
        spent=spent,
        balance=earned - spent,
        budgets=stats.budget_progress(budgets, expenses),
        colors=COLORS,
        recent=stats.recent_transactions(expenses, income),
        chart_data=chart_data(expenses),
        has_expenses=bool(expenses),
        categories=CATEGORIES,
        # quick add uses today, or the 1st when looking at another month
        default_date=today.isoformat() if month.contains(today.isoformat()) else month.start,
        next_url=request.full_path.rstrip("?"),
    )
