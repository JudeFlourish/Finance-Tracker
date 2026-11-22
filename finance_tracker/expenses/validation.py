from ..validation import parse_amount, parse_category, parse_date, parse_text
from .models import Expense


def validate_expense(form):
    """Turn raw form values into an Expense, or raise ValidationError.

    Used by add, edit and the JSON importer, so the rules are the same everywhere.
    """
    return Expense(
        description=parse_text(form.get("description"), "Please write a description"),
        amount=parse_amount(form.get("amount")),
        date=parse_date(form.get("date")),
        category=parse_category(form.get("category")),
    )
