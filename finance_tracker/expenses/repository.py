from sqlalchemy import asc, desc, select

from ..repository import Repository
from .filters import ExpenseFilter
from .models import Expense


class ExpenseRepository(Repository):
    """All database access for expenses."""

    def add(self, expense):
        self.session.add(expense)
        self._commit()
        return expense.id  # the database gives the id on commit

    def add_many(self, expenses):
        """Insert all of them in one transaction: either every row is saved or none."""
        self.session.add_all(expenses)
        self._commit()
        return len(expenses)

    def get(self, expense_id):
        return self.session.get(Expense, expense_id)

    def update(self, expense):
        """Save expense's values onto the stored expense with the same id.
        Returns False when there is no expense with that id."""
        saved = self.get(expense.id)
        if saved is None:
            return False
        saved.description = expense.description
        saved.amount = expense.amount
        saved.date = expense.date
        saved.category = expense.category
        self._commit()  # SQLAlchemy sees which attributes changed and writes the UPDATE
        return True

    def delete(self, expense_id):
        """Returns False when there is no expense with that id."""
        saved = self.get(expense_id)
        if saved is None:
            return False
        self.session.delete(saved)
        self._commit()
        return True

    def list(self, expense_filter=ExpenseFilter(), newest_first=True):
        order = desc if newest_first else asc
        query = (
            select(Expense)
            .where(*expense_filter.conditions())
            # id as a second sort key keeps expenses on the same day in a fixed order
            .order_by(order(Expense.date), order(Expense.id))
        )
        return list(self.session.scalars(query))
