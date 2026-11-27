import sqlite3

import pytest

from finance_tracker.expenses.filters import ExpenseFilter
from finance_tracker.expenses.models import Expense
from finance_tracker.expenses.repository import ExpenseRepository
from finance_tracker.expenses.validation import validate_expense
from finance_tracker.validation import ValidationError


def make(description="Lunch", amount=12.5, date="2026-11-05", category="Food"):
    return Expense(description=description, amount=amount, date=date, category=category)


@pytest.fixture
def repo(conn):
    return ExpenseRepository(conn)


@pytest.fixture
def sample(repo):
    # three expenses over three days, in two categories
    repo.add(make("Lunch", 12.5, "2026-11-01", "Food"))
    repo.add(make("Bus", 3, "2026-11-05", "Transport"))
    repo.add(make("Dinner", 20, "2026-11-10", "Food"))
    return repo


def descriptions(expenses):
    return [e.description for e in expenses]


# add / get

def test_add_returns_id_and_get_reads_it_back(repo):
    new_id = repo.add(make())
    assert repo.get(new_id).to_dict() == {
        "id": new_id, "description": "Lunch", "amount": 12.5, "date": "2026-11-05", "category": "Food",
    }


def test_get_unknown_id_returns_none(repo):
    assert repo.get(99) is None


def test_add_rejected_by_database_saves_nothing(repo):
    # the CHECK constraint stops a zero amount even if validation is skipped
    with pytest.raises(sqlite3.IntegrityError):
        repo.add(make(amount=0))
    assert repo.list() == []


# add_many

def test_add_many_saves_all(repo):
    assert repo.add_many([make("A"), make("B")]) == 2
    assert sorted(descriptions(repo.list())) == ["A", "B"]


def test_add_many_saves_nothing_if_one_row_is_bad(repo):
    with pytest.raises(sqlite3.IntegrityError):
        repo.add_many([make("A"), make("B", amount=-1)])
    assert repo.list() == []


# update

def test_update_changes_every_field(repo):
    new_id = repo.add(make())
    changed = Expense(id=new_id, description="Brunch", amount=9, date="2026-11-06", category="Other")
    assert repo.update(changed) is True
    assert repo.get(new_id).to_dict() == changed.to_dict()


def test_update_unknown_id_returns_false(repo):
    expense = make()
    expense.id = 99
    assert repo.update(expense) is False


# delete

def test_delete_removes_only_that_expense(sample):
    first = sample.list(newest_first=False)[0]
    assert sample.delete(first.id) is True
    assert descriptions(sample.list()) == ["Dinner", "Bus"]


def test_delete_unknown_id_returns_false(repo):
    assert repo.delete(99) is False


# list and filters

def test_list_newest_first_by_default(sample):
    assert descriptions(sample.list()) == ["Dinner", "Bus", "Lunch"]


def test_list_oldest_first(sample):
    assert descriptions(sample.list(newest_first=False)) == ["Lunch", "Bus", "Dinner"]


def test_same_day_keeps_a_fixed_order(repo):
    repo.add(make("First", date="2026-11-05"))
    repo.add(make("Second", date="2026-11-05"))
    assert descriptions(repo.list()) == ["Second", "First"]


@pytest.mark.parametrize("expense_filter, expected", [
    (ExpenseFilter(), ["Dinner", "Bus", "Lunch"]),
    (ExpenseFilter(start="2026-11-05"), ["Dinner", "Bus"]),
    (ExpenseFilter(end="2026-11-05"), ["Bus", "Lunch"]),
    (ExpenseFilter(start="2026-11-02", end="2026-11-09"), ["Bus"]),
    (ExpenseFilter(category="Food"), ["Dinner", "Lunch"]),
    (ExpenseFilter(start="2026-11-05", category="Food"), ["Dinner"]),
    (ExpenseFilter(category="Rent"), []),
])
def test_list_with_filter(sample, expense_filter, expected):
    assert descriptions(sample.list(expense_filter)) == expected


# ExpenseFilter.from_args

def test_filter_from_args_reads_values():
    f = ExpenseFilter.from_args({"start": "2026-11-01", "end": "2026-11-30", "category": "Food"})
    assert f == ExpenseFilter("2026-11-01", "2026-11-30", "Food")


def test_filter_from_args_defaults():
    assert ExpenseFilter.from_args({}) == ExpenseFilter("", "", "All")


@pytest.mark.parametrize("args", [
    {"start": "2026-02-30"},
    {"end": "yesterday"},
    {"category": "Pizza"},
    {"category": "Food' OR 1=1 --"},
])
def test_filter_from_args_ignores_bad_values(args):
    assert ExpenseFilter.from_args(args) == ExpenseFilter()


def test_filter_to_sql_uses_parameters():
    where, params = ExpenseFilter("2026-11-01", "", "Food").to_sql()
    assert where == " WHERE date >= ? AND category = ?"
    assert params == ["2026-11-01", "Food"]


def test_filter_as_args():
    f = ExpenseFilter("2026-11-01", "", "Food")
    assert f.as_args() == {"start": "2026-11-01", "end": "", "category": "Food"}


# validate_expense

def test_validate_expense_builds_expense():
    expense = validate_expense({
        "description": " Bus ", "amount": "3", "date": "2026-11-05", "category": "Pizza",
    })
    assert expense.to_dict() == {
        "id": None, "description": "Bus", "amount": 3.0, "date": "2026-11-05", "category": "Other",
    }


@pytest.mark.parametrize("form, message", [
    ({"description": "", "amount": "3"}, "Please write a description"),
    ({"description": "Bus", "amount": "abc"}, "Amount must be a number"),
    ({"description": "Bus", "amount": "0"}, "Please enter a positive number"),
    ({"description": "Bus", "amount": "3", "date": "2026-02-30"}, "Please enter a valid date"),
])
def test_validate_expense_rejects_bad_forms(form, message):
    with pytest.raises(ValidationError, match=message):
        validate_expense(form)
