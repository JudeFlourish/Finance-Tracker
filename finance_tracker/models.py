"""Base model shared by expenses and income."""
from dataclasses import dataclass


# kw_only: id has a default value, and without kw_only a subclass could not
# add fields without defaults (like Expense.description) after it
@dataclass(kw_only=True)
class Entry:
    """Any amount of money on a date. Expense and Income extend this."""
    amount: float
    date: str  # ISO "YYYY-MM-DD", so dates sort and compare as strings
    id: int | None = None


def total(entries):
    # works for expenses and income alike, because both are entries
    return sum(e.amount for e in entries)
