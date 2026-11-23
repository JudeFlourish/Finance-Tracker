from datetime import date

import pytest

from finance_tracker.dashboard.stats import Month, Transaction, parse_month, recent_transactions
from finance_tracker.expenses.models import Expense
from finance_tracker.expenses.repository import ExpenseRepository
from finance_tracker.income.models import Income
from finance_tracker.income.repository import IncomeRepository

TODAY = date(2026, 11, 23)


# Month

@pytest.mark.parametrize("month, start, end", [
    (Month(2026, 11), "2026-11-01", "2026-11-30"),
    (Month(2026, 12), "2026-12-01", "2026-12-31"),
    (Month(2028, 2), "2028-02-01", "2028-02-29"),  # leap year
    (Month(2026, 2), "2026-02-01", "2026-02-28"),
])
def test_month_first_and_last_day(month, start, end):
    assert (month.start, month.end) == (start, end)


def test_month_label_and_param():
    assert Month(2026, 3).label == "March 2026"
    assert Month(2026, 3).param == "2026-03"


def test_previous_and_next_cross_the_year():
    assert Month(2026, 1).previous() == Month(2025, 12)
    assert Month(2026, 12).next() == Month(2027, 1)
    assert Month(2026, 6).previous() == Month(2026, 5)
    assert Month(2026, 6).next() == Month(2026, 7)


def test_month_contains():
    november = Month(2026, 11)
    assert november.contains("2026-11-01") and november.contains("2026-11-30")
    assert not november.contains("2026-10-31") and not november.contains("2026-12-01")


@pytest.mark.parametrize("value, expected", [
    ("2026-03", Month(2026, 3)),
    ("2025-12", Month(2025, 12)),
    (None, Month(2026, 11)),
    ("", Month(2026, 11)),
    ("2026-13", Month(2026, 11)),
    ("2026-00", Month(2026, 11)),
    ("march", Month(2026, 11)),
    ("2026-03-01", Month(2026, 11)),
])
def test_parse_month_falls_back_to_current_month(value, expected):
    assert parse_month(value, TODAY) == expected


# recent_transactions

def test_recent_mixes_expenses_and_income_newest_first():
    expenses = [
        Expense(description="Lunch", amount=12.5, date="2026-11-05", category="Food"),
        Expense(description="Bus", amount=3, date="2026-11-01", category="Transport"),
    ]
    income = [Income(source="Salary", amount=1500, date="2026-11-03")]
    assert recent_transactions(expenses, income) == [
        Transaction("expense", "2026-11-05", "Lunch", "Food", 12.5),
        Transaction("income", "2026-11-03", "Salary", "Income", 1500),
        Transaction("expense", "2026-11-01", "Bus", "Transport", 3),
    ]


def test_recent_keeps_only_the_newest_five():
    expenses = [Expense(description=f"E{d}", amount=1, date=f"2026-11-{d:02d}", category="Food")
                for d in range(1, 9)]
    recent = recent_transactions(expenses, [])
    assert [t.label for t in recent] == ["E8", "E7", "E6", "E5", "E4"]


# the page

@pytest.fixture
def november(conn):
    # October and November data, so the page must pick the right month
    expenses = ExpenseRepository(conn)
    income = IncomeRepository(conn)
    expenses.add(Expense(description="Rent", amount=700, date="2026-11-01", category="Rent"))
    expenses.add(Expense(description="Lunch", amount=12.5, date="2026-11-05", category="Food"))
    expenses.add(Expense(description="Old lunch", amount=99, date="2026-10-20", category="Food"))
    income.add(Income(source="Salary", amount=1500, date="2026-11-03"))
    income.add(Income(source="Old salary", amount=1000, date="2026-10-03"))


def test_month_totals_and_balance(client, november):
    page = client.get("/?month=2026-11").get_data(as_text=True)
    assert "<h1>November 2026</h1>" in page
    assert "$1500.00" in page   # income
    assert "$712.50" in page    # spending
    assert "$787.50" in page    # balance = 1500 - 712.50
    assert "Old lunch" not in page and "Old salary" not in page


def test_empty_month_has_zero_balance(client, november):
    page = client.get("/?month=2026-12").get_data(as_text=True)
    balance = page.split("<h2>Balance</h2>")[1].split("</section>")[0]
    assert "$0.00" in balance
    assert "negative" not in balance


def test_balance_below_zero(client, conn):
    ExpenseRepository(conn).add(Expense(description="Rent", amount=700, date="2026-11-01", category="Rent"))
    IncomeRepository(conn).add(Income(source="Gift", amount=200, date="2026-11-02"))
    page = client.get("/?month=2026-11").get_data(as_text=True)
    balance = page.split("<h2>Balance</h2>")[1].split("</section>")[0]
    assert 'class="stat-value negative"' in balance
    assert "-$500.00" in balance


def test_recent_activity_on_page(client, november):
    page = client.get("/?month=2026-11").get_data(as_text=True)
    assert "<td>Salary</td>" in page and "+$1500.00" in page
    assert "<td>Lunch</td>" in page and "-$12.50" in page


def test_empty_month(client):
    page = client.get("/?month=2026-12").get_data(as_text=True)
    assert "Nothing in December 2026 yet." in page
    assert "No spending this month" in page


def test_charts_use_expenses_of_the_month_only(client, november):
    page = client.get("/?month=2026-11").get_data(as_text=True)
    chart = page.split("const chartData = ")[1].split(";")[0]
    # only November's expenses: no income (1500) and no October lunch (99)
    assert '"pie_labels": ["Food", "Rent"]' in chart
    assert '"pie_values": [12.5, 700.0]' in chart
    assert '"bar_labels": ["2026-11-01", "2026-11-05"]' in chart


def test_month_links(client):
    page = client.get("/?month=2026-01").get_data(as_text=True)
    assert 'href="/?month=2025-12"' in page
    assert 'href="/?month=2026-02"' in page
    assert "Back to this month" in page


def test_bad_month_shows_current_month(client):
    response = client.get("/?month=nonsense")
    assert response.status_code == 200
    assert f"<h1>{Month(date.today().year, date.today().month).label}</h1>" in response.get_data(as_text=True)


def test_quick_add_forms_come_back_to_dashboard(client):
    page = client.get("/?month=2026-11").get_data(as_text=True)
    assert 'action="/expenses/add"' in page
    assert 'action="/income/"' in page
    assert page.count('name="next" value="/?month=2026-11"') == 2
    # two forms on one page, so their fields need different ids
    assert 'id="expense-amount"' in page and 'id="income-amount"' in page


def test_quick_add_date_is_first_of_other_month(client):
    page = client.get("/?month=2020-05").get_data(as_text=True)
    assert 'value="2020-05-01"' in page


def test_quick_add_expense_and_income(client, conn):
    client.post("/expenses/add", data={
        "description": "Lunch", "amount": "10", "date": "2026-11-05", "category": "Food", "next": "/?month=2026-11",
    })
    response = client.post("/income/", data={
        "source": "Salary", "amount": "100", "date": "2026-11-06", "next": "/?month=2026-11",
    })
    assert response.location == "/?month=2026-11"
    page = client.get("/?month=2026-11").get_data(as_text=True)
    assert "$90.00" in page  # balance
