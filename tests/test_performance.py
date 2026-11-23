import time

from finance_tracker.categories import CATEGORIES
from finance_tracker.expenses.models import Expense
from finance_tracker.expenses.repository import ExpenseRepository

# US-02: pages must load in under 2 seconds with 1,000 expenses


def add_1000_expenses(conn, month=None):
    # spread over the year, or all in one month ("2026-11") for the dashboard
    ExpenseRepository(conn).add_many([
        Expense(
            description=f"Expense {i}",
            amount=i % 200 + 1,
            date=f"{month or f'2026-{i % 11 + 1:02d}'}-{i % 28 + 1:02d}",
            category=CATEGORIES[i % len(CATEGORIES)],
        )
        for i in range(1000)
    ])


def timed_get(client, url):
    start = time.perf_counter()
    response = client.get(url)
    return response, time.perf_counter() - start


def test_expenses_page_under_2_seconds_with_1000_expenses(client, conn):
    add_1000_expenses(conn)
    response, seconds = timed_get(client, "/expenses/")
    assert response.status_code == 200
    assert response.get_data(as_text=True).count("Expense ") >= 1000
    assert seconds < 2, f"expenses page took {seconds:.2f} s"


def test_dashboard_under_2_seconds_with_1000_expenses_in_the_month(client, conn):
    add_1000_expenses(conn, month="2026-11")
    response, seconds = timed_get(client, "/?month=2026-11")
    assert response.status_code == 200
    assert "Expense " in response.get_data(as_text=True)
    assert seconds < 2, f"dashboard took {seconds:.2f} s"
