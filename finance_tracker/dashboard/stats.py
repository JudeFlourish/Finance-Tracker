"""Numbers for the dashboard. Plain functions: plain lists in, plain values out.

Nothing here touches Flask or the database, so it is easy to test.
"""
import calendar
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Month:
    year: int
    month: int

    @property
    def start(self):
        """First day, "YYYY-MM-01"."""
        return date(self.year, self.month, 1).isoformat()

    @property
    def end(self):
        """Last day; calendar knows how long each month is, leap years too."""
        last_day = calendar.monthrange(self.year, self.month)[1]
        return date(self.year, self.month, last_day).isoformat()

    @property
    def label(self):
        return f"{calendar.month_name[self.month]} {self.year}"

    @property
    def param(self):
        """For the url, e.g. ?month=2026-11"""
        return f"{self.year:04d}-{self.month:02d}"

    def previous(self):
        return Month(self.year - 1, 12) if self.month == 1 else Month(self.year, self.month - 1)

    def next(self):
        return Month(self.year + 1, 1) if self.month == 12 else Month(self.year, self.month + 1)

    def contains(self, day):
        """day is a "YYYY-MM-DD" string."""
        return self.start <= day <= self.end


def parse_month(value, today):
    """ "2026-11" -> Month. Anything else falls back to the current month,
    so a broken link still shows a page."""
    try:
        year, month = (int(part) for part in (value or "").split("-"))
        if 1 <= year <= 9999 and 1 <= month <= 12:
            return Month(year, month)
    except ValueError:
        pass
    return Month(today.year, today.month)


@dataclass(frozen=True)
class Transaction:
    """One line in "recent activity": an expense or an income."""
    kind: str  # "expense" or "income"
    date: str
    label: str
    detail: str
    amount: float


def recent_transactions(expenses, income, limit=5):
    items = [Transaction("expense", e.date, e.description, e.category, e.amount) for e in expenses]
    items += [Transaction("income", i.date, i.source, "Income", i.amount) for i in income]
    # sort is stable, so on the same day the order the repositories gave is kept
    items.sort(key=lambda t: t.date, reverse=True)
    return items[:limit]
