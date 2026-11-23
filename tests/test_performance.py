import time

from finance_tracker.categories import CATEGORIES
from finance_tracker.expenses.models import Expense
from finance_tracker.expenses.repository import ExpenseRepository


def test_dashboard_loads_under_2_seconds_with_1000_expenses(client, conn):
    # US-02: the dashboard must load in under 2 seconds with 1,000 expenses
    ExpenseRepository(conn).add_many([
        Expense(
            description=f"Expense {i}",
            amount=i % 200 + 1,
            date=f"2026-{i % 11 + 1:02d}-{i % 28 + 1:02d}",
            category=CATEGORIES[i % len(CATEGORIES)],
        )
        for i in range(1000)
    ])

    start = time.perf_counter()
    response = client.get("/expenses/")
    seconds = time.perf_counter() - start

    assert response.status_code == 200
    assert response.get_data(as_text=True).count("Expense ") >= 1000
    assert seconds < 2, f"dashboard took {seconds:.2f} s"
