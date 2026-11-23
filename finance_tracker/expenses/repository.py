from .filters import ExpenseFilter
from .models import Expense

# named columns instead of SELECT *, so adding a column to the table
# later doesn't change what these queries return
_COLUMNS = "id, description, amount, date, category"


def _to_expense(row):
    return Expense(
        id=row["id"],
        description=row["description"],
        amount=row["amount"],
        date=row["date"],
        category=row["category"],
    )


class ExpenseRepository:
    """All SQL for the expenses table. Gets its connection from outside,
    so tests can pass in a temporary database."""

    def __init__(self, conn):
        self.conn = conn

    def add(self, expense):
        with self.conn:  # one transaction: commits, or rolls back on error
            cursor = self.conn.execute(
                "INSERT INTO expenses (description, amount, date, category) VALUES (?, ?, ?, ?)",
                (expense.description, expense.amount, expense.date, expense.category),
            )
        return cursor.lastrowid

    def add_many(self, expenses):
        """Insert all of them in one transaction: either every row is saved or none."""
        with self.conn:
            self.conn.executemany(
                "INSERT INTO expenses (description, amount, date, category) VALUES (?, ?, ?, ?)",
                [(e.description, e.amount, e.date, e.category) for e in expenses],
            )
        return len(expenses)

    def get(self, expense_id):
        row = self.conn.execute(
            f"SELECT {_COLUMNS} FROM expenses WHERE id = ?", (expense_id,)
        ).fetchone()
        return _to_expense(row) if row else None

    def update(self, expense):
        """Returns False when there is no expense with that id."""
        with self.conn:
            cursor = self.conn.execute(
                "UPDATE expenses SET description = ?, amount = ?, date = ?, category = ? WHERE id = ?",
                (expense.description, expense.amount, expense.date, expense.category, expense.id),
            )
        return cursor.rowcount > 0

    def delete(self, expense_id):
        """Returns False when there is no expense with that id."""
        with self.conn:
            cursor = self.conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        return cursor.rowcount > 0

    def list(self, expense_filter=ExpenseFilter(), newest_first=True):
        where, params = expense_filter.to_sql()
        order = "DESC" if newest_first else "ASC"
        # id as a second sort key keeps expenses on the same day in a fixed order
        rows = self.conn.execute(
            f"SELECT {_COLUMNS} FROM expenses{where} ORDER BY date {order}, id {order}", params
        ).fetchall()
        return [_to_expense(r) for r in rows]
