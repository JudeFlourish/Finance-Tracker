from sqlalchemy import select

from ..repository import Repository
from .models import Income


class IncomeRepository(Repository):
    """All database access for income."""

    def add(self, income):
        self.session.add(income)
        self._commit()
        return income.id  # the database gives the id on commit

    def get(self, income_id):
        return self.session.get(Income, income_id)

    def delete(self, income_id):
        """Returns False when there is no income with that id."""
        saved = self.get(income_id)
        if saved is None:
            return False
        self.session.delete(saved)
        self._commit()
        return True

    def list(self, start="", end=""):
        """Newest first. start and end are optional "YYYY-MM-DD" dates, both included,
        so the dashboard can ask for one month."""
        query = select(Income)
        if start:
            query = query.where(Income.date >= start)
        if end:
            query = query.where(Income.date <= end)
        # id as a second sort key keeps income on the same day in a fixed order
        query = query.order_by(Income.date.desc(), Income.id.desc())
        return list(self.session.scalars(query))
