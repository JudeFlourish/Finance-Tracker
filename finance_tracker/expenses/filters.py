from dataclasses import dataclass

from ..categories import CATEGORIES
from ..validation import ValidationError, parse_date

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

    def to_sql(self):
        """The WHERE clause and its parameters.

        Values are always passed as ? parameters, never put into the SQL text,
        so nothing typed in the url can change the query.
        """
        conditions, params = [], []
        if self.start:
            conditions.append("date >= ?")
            params.append(self.start)
        if self.end:
            conditions.append("date <= ?")
            params.append(self.end)
        if self.category != ALL:
            conditions.append("category = ?")
            params.append(self.category)
        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        return where, params

    def as_args(self):
        """For building links (e.g. the CSV export) that keep the current filter."""
        return {"start": self.start, "end": self.end, "category": self.category}
