from sqlalchemy import select

from ..categories import CATEGORIES
from ..repository import Repository
from .models import Budget


class BudgetRepository(Repository):
    """All database access for budgets."""

    def save(self, budget):
        """Create the category's budget, or change its limit if it already has one.

        There is only ever one budget per category (unique in budgets/models.py),
        so setting a budget again is the same as changing it.
        """
        saved = self.get_by_category(budget.category)
        if saved is None:
            self.session.add(budget)
        else:
            saved.monthly_limit = budget.monthly_limit
        self._commit()

    def get_by_category(self, category):
        return self.session.scalars(select(Budget).where(Budget.category == category)).first()

    def delete(self, budget_id):
        """Returns False when there is no budget with that id."""
        saved = self.session.get(Budget, budget_id)
        if saved is None:
            return False
        self.session.delete(saved)
        self._commit()
        return True

    def list(self):
        """All budgets, in the same order as the categories list."""
        order = {c: i for i, c in enumerate(CATEGORIES)}
        budgets = self.session.scalars(select(Budget))
        # a category not in the list (shouldn't happen) goes last instead of crashing
        return sorted(budgets, key=lambda b: order.get(b.category, len(order)))
