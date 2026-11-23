"""Field parsers shared by every feature's validation.

They take raw form values (strings) and either return a clean value or raise
ValidationError with a message that can be shown to the user. No Flask here,
so they can be tested on their own.
"""
import math
from datetime import date, datetime

from .categories import CATEGORIES, DEFAULT_CATEGORY


class ValidationError(ValueError):
    pass


def parse_text(value, message):
    # forms always send strings, but an imported file can hold anything
    if not isinstance(value, str) or value.strip() == "":
        raise ValidationError(message)
    return value.strip()


def parse_amount(value, field="Amount"):
    # float(True) is 1.0, so a true/false value would pass as an amount
    if isinstance(value, bool):
        raise ValidationError(f"{field} must be a number")
    try:
        amount = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field} must be a number")
    # float() also accepts "nan" and "inf", which are not real amounts
    if not math.isfinite(amount) or amount <= 0:
        raise ValidationError("Please enter a positive number")
    return amount


def parse_date(value):
    """Return the date as "YYYY-MM-DD". An empty value means today."""
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise ValidationError("Please enter a valid date")
    value = value.strip()
    if value == "":
        return date.today().isoformat()
    try:
        day = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError("Please enter a valid date")
    # strptime also accepts "2026-1-5", but we store dates zero-padded
    # so they keep sorting correctly as strings
    if day.isoformat() != value:
        raise ValidationError("Please enter a valid date")
    return value


def parse_category(value, strict=False):
    """Return a known category.

    An unknown one becomes "Other" (expenses, same as before), or with
    strict=True is refused (budgets: a budget needs a real category).
    """
    if value in CATEGORIES:
        return value
    if strict:
        raise ValidationError("Please choose a category")
    return DEFAULT_CATEGORY
