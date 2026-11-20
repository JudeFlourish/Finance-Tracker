"""Base model shared by expenses and income."""
from dataclasses import dataclass


@dataclass(kw_only=True)
class Entry:
    """Any amount of money on a date. Expense and Income extend this."""
    amount: float
    date: str  # ISO "YYYY-MM-DD", so dates sort and compare as strings
    id: int | None = None


def total(entries):
    # works for expenses and income alike, because both are entries
    return sum(e.amount for e in entries)
