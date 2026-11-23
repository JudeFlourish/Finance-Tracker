from .models import Income

# named columns instead of SELECT *, so adding a column to the table
# later doesn't change what these queries return
_COLUMNS = "id, source, amount, date"


def _to_income(row):
    return Income(id=row["id"], source=row["source"], amount=row["amount"], date=row["date"])


class IncomeRepository:
    """All SQL for the income table. Gets its connection from outside,
    so tests can pass in a temporary database."""

    def __init__(self, conn):
        self.conn = conn

    def add(self, income):
        with self.conn:  # one transaction: commits, or rolls back on error
            cursor = self.conn.execute(
                "INSERT INTO income (source, amount, date) VALUES (?, ?, ?)",
                (income.source, income.amount, income.date),
            )
        return cursor.lastrowid

    def get(self, income_id):
        row = self.conn.execute(
            f"SELECT {_COLUMNS} FROM income WHERE id = ?", (income_id,)
        ).fetchone()
        return _to_income(row) if row else None

    def delete(self, income_id):
        """Returns False when there is no income with that id."""
        with self.conn:
            cursor = self.conn.execute("DELETE FROM income WHERE id = ?", (income_id,))
        return cursor.rowcount > 0

    def list(self, start="", end=""):
        """Newest first. start and end are optional "YYYY-MM-DD" dates, both included,
        so the dashboard can ask for one month."""
        conditions, params = [], []
        if start:
            conditions.append("date >= ?")
            params.append(start)
        if end:
            conditions.append("date <= ?")
            params.append(end)
        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        # id as a second sort key keeps income on the same day in a fixed order
        rows = self.conn.execute(
            f"SELECT {_COLUMNS} FROM income{where} ORDER BY date DESC, id DESC", params
        ).fetchall()
        return [_to_income(r) for r in rows]
