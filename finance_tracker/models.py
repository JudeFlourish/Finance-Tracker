"""Base model shared by expenses and income."""
from sqlalchemy import CheckConstraint, Float, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import db


class Entry(db.Model):
    """Any amount of money on a date. Expense and Income extend this.

    __abstract__: Entry has no table of its own, every subclass gets these
    columns in its own table.
    """
    __abstract__ = True

    # sort_order: id comes first in the table, before the subclass columns
    id: Mapped[int] = mapped_column(primary_key=True, sort_order=-1)
    amount: Mapped[float] = mapped_column(Float)
    date: Mapped[str] = mapped_column(Text)  # ISO "YYYY-MM-DD", so dates sort and compare as strings


def entry_checks():
    """Rules every entry table has. A function, because each table needs its own copy."""
    return (
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint("date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'", name="date_format"),
    )


def not_blank(column):
    return CheckConstraint(f"length(trim({column})) > 0", name=f"{column}_not_blank")


def total(entries):
    # works for expenses and income alike, because both are entries
    return sum(e.amount for e in entries)
