from dataclasses import dataclass

from ..categories import CATEGORIES
from ..validation import ValidationError, parse_date
from .models import Expense

ALL = "All"


def _date_or_empty(value):
    # a broken date in the url is ignored instead of crashing the page
    if not value:
        return ""
    try:
        return parse_date(value)
    except ValidationError:
        return ""


# frozen: a filter can't be changed after it is made, so one ExpenseFilter()
# can safely be shared as a default value (see ExpenseRepository.list)
@dataclass(frozen=True)
class ExpenseFilter:
    """Which expenses to show. Filters come from the url so a view can be bookmarked."""
    start: str = ""
    end: str = ""
    category: str = ALL

    @classmethod
    def from_args(cls, args):
        category = args.get("category", ALL)
        if category not in CATEGORIES:
            category = ALL
        return cls(
            start=_date_or_empty(args.get("start", "")),
            end=_date_or_empty(args.get("end", "")),
            category=category,
        )

    def conditions(self):
        """The WHERE conditions, for select(Expense).where(*conditions).

        SQLAlchemy always sends the values as bound parameters, never inside
        the SQL text, so nothing typed in the url can change the query.
        """
        conditions = []
        if self.start:
            conditions.append(Expense.date >= self.start)
        if self.end:
            conditions.append(Expense.date <= self.end)
        if self.category != ALL:
            conditions.append(Expense.category == self.category)
        return conditions

    def as_args(self):
        """For building links (e.g. the CSV export) that keep the current filter."""
        return {"start": self.start, "end": self.end, "category": self.category}
