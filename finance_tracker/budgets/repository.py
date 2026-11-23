from ..categories import CATEGORIES
from .models import Budget

# named columns instead of SELECT *, so adding a column to the table
# later doesn't change what these queries return
_COLUMNS = "id, category, monthly_limit"


def _to_budget(row):
    return Budget(id=row["id"], category=row["category"], monthly_limit=row["monthly_limit"])


class BudgetRepository:
    """All SQL for the budgets table. Gets its connection from outside,
    so tests can pass in a temporary database."""

    def __init__(self, conn):
        self.conn = conn

    def save(self, budget):
        """Create the category's budget, or change its limit if it already has one.

        There is only ever one budget per category (UNIQUE in schema.sql),
        so setting a budget again is the same as changing it.
        """
        with self.conn:  # one transaction: commits, or rolls back on error
            self.conn.execute(
                "INSERT INTO budgets (category, monthly_limit) VALUES (?, ?) "
                "ON CONFLICT (category) DO UPDATE SET monthly_limit = excluded.monthly_limit",
                (budget.category, budget.monthly_limit),
            )

    def get_by_category(self, category):
        row = self.conn.execute(
            f"SELECT {_COLUMNS} FROM budgets WHERE category = ?", (category,)
        ).fetchone()
        return _to_budget(row) if row else None

    def delete(self, budget_id):
        """Returns False when there is no budget with that id."""
        with self.conn:
            cursor = self.conn.execute("DELETE FROM budgets WHERE id = ?", (budget_id,))
        return cursor.rowcount > 0

    def list(self):
        """All budgets, in the same order as the categories list."""
        rows = self.conn.execute(f"SELECT {_COLUMNS} FROM budgets").fetchall()
        order = {c: i for i, c in enumerate(CATEGORIES)}
        # a category not in the list (shouldn't happen) goes last instead of crashing
        return sorted((_to_budget(r) for r in rows), key=lambda b: order.get(b.category, len(order)))
