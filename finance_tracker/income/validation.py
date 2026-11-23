from ..validation import parse_amount, parse_date, parse_text
from .models import Income


def validate_income(form):
    """Turn raw form values into an Income, or raise ValidationError."""
    return Income(
        source=parse_text(form.get("source"), "Please write where the income came from"),
        amount=parse_amount(form.get("amount")),
        date=parse_date(form.get("date")),
    )
