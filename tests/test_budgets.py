import sqlite3

import pytest

from finance_tracker import create_app
from finance_tracker.budgets.models import Budget
from finance_tracker.budgets.repository import BudgetRepository
from finance_tracker.budgets.validation import validate_budget
from finance_tracker.expenses.models import Expense
from finance_tracker.expenses.repository import ExpenseRepository
from finance_tracker.validation import ValidationError


@pytest.fixture
def repo(conn):
    return BudgetRepository(conn)


# create, change, delete

def test_save_creates_budget(repo):
    repo.save(Budget(category="Food", monthly_limit=300))
    budget = repo.get_by_category("Food")
    assert budget == Budget(id=budget.id, category="Food", monthly_limit=300)


def test_get_by_category_without_budget_returns_none(repo):
    assert repo.get_by_category("Rent") is None


def test_save_again_changes_the_limit(repo):
    repo.save(Budget(category="Food", monthly_limit=300))
    first = repo.get_by_category("Food")
    repo.save(Budget(category="Food", monthly_limit=250.5))
    assert repo.list() == [Budget(id=first.id, category="Food", monthly_limit=250.5)]


def test_delete_removes_budget(repo):
    repo.save(Budget(category="Food", monthly_limit=300))
    repo.save(Budget(category="Rent", monthly_limit=700))
    assert repo.delete(repo.get_by_category("Food").id) is True
    assert [b.category for b in repo.list()] == ["Rent"]


def test_delete_unknown_id_returns_false(repo):
    assert repo.delete(99) is False


def test_delete_budget_keeps_expenses(conn, repo):
    expenses = ExpenseRepository(conn)
    expenses.add(Expense(description="Lunch", amount=12.5, date="2026-11-01", category="Food"))
    repo.save(Budget(category="Food", monthly_limit=300))
    repo.delete(repo.get_by_category("Food").id)
    assert [e.description for e in expenses.list()] == ["Lunch"]


def test_list_follows_category_order(repo):
    for category in ["Other", "Food", "Health"]:
        repo.save(Budget(category=category, monthly_limit=100))
    assert [b.category for b in repo.list()] == ["Food", "Health", "Other"]


def test_list_empty(repo):
    assert repo.list() == []


# database rules, even if validation is skipped

@pytest.mark.parametrize("limit", [0, -10])
def test_database_rejects_limit_of_zero_or_less(repo, limit):
    with pytest.raises(sqlite3.IntegrityError):
        repo.save(Budget(category="Food", monthly_limit=limit))
    assert repo.list() == []


def test_database_allows_one_budget_per_category(conn):
    conn.execute("INSERT INTO budgets (category, monthly_limit) VALUES ('Food', 100)")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO budgets (category, monthly_limit) VALUES ('Food', 200)")


def test_existing_database_gets_budgets_table_on_start(tmp_path):
    # a database made before budgets existed: only the expenses table, with data
    path = tmp_path / "old.db"
    old = sqlite3.connect(path)
    old.execute("CREATE TABLE expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, description TEXT, "
                "amount REAL, date TEXT, category TEXT)")
    old.execute("INSERT INTO expenses (description, amount, date, category) "
                "VALUES ('Lunch', 12.5, '2026-11-01', 'Food')")
    old.commit()
    old.close()

    create_app({"TESTING": True, "DATABASE": str(path)})  # what starting the app does

    conn = sqlite3.connect(path)
    tables = {name for (name,) in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert "budgets" in tables
    assert conn.execute("SELECT description FROM expenses").fetchall() == [("Lunch",)]
    conn.close()


# validate_budget

def test_validate_budget():
    assert validate_budget({"category": "Food", "monthly_limit": "300"}) == Budget(
        category="Food", monthly_limit=300.0,
    )


@pytest.mark.parametrize("form, message", [
    ({"category": "Pizza", "monthly_limit": "300"}, "Please choose a category"),
    ({"category": "", "monthly_limit": "300"}, "Please choose a category"),
    ({"monthly_limit": "300"}, "Please choose a category"),
    ({"category": "Food", "monthly_limit": "abc"}, "Budget must be a number"),
    ({"category": "Food", "monthly_limit": ""}, "Budget must be a number"),
    ({"category": "Food", "monthly_limit": "0"}, "Please enter a positive number"),
    ({"category": "Food", "monthly_limit": "-50"}, "Please enter a positive number"),
])
def test_validate_budget_rejects_bad_forms(form, message):
    with pytest.raises(ValidationError, match=message):
        validate_budget(form)
