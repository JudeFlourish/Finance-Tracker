import json

import pytest

from finance_tracker.expenses.models import Expense
from finance_tracker.expenses.repository import ExpenseRepository

# exactly what the old app wrote to expenses.json (json.dump with indent=4)
OLD_FILE = """[
    {
        "id": 1,
        "description": "Lunch",
        "amount": 12.5,
        "date": "2026-11-01",
        "category": "Food"
    },
    {
        "id": 4,
        "description": "Bus",
        "amount": 3.0,
        "date": "2026-11-05",
        "category": "Transport"
    }
]"""


@pytest.fixture
def run_import(app, tmp_path):
    """Write content to a file and run `flask import-json` on it."""
    def _run(content, name="expenses.json"):
        path = tmp_path / name
        if content is not None:
            path.write_text(content if isinstance(content, str) else json.dumps(content))
        return app.test_cli_runner().invoke(args=["import-json", str(path)])
    return _run


def saved(conn):
    return ExpenseRepository(conn).list(newest_first=False)


def good(**fields):
    record = {"id": 1, "description": "Lunch", "amount": 12.5, "date": "2026-11-01", "category": "Food"}
    record.update(fields)
    return record


def test_imports_old_file_with_same_values(run_import, conn):
    result = run_import(OLD_FILE)
    assert result.exit_code == 0
    assert result.output.strip() == "Imported 2 expenses."
    assert saved(conn) == [
        Expense(id=1, description="Lunch", amount=12.5, date="2026-11-01", category="Food"),
        Expense(id=2, description="Bus", amount=3.0, date="2026-11-05", category="Transport"),
    ]


def test_empty_list_imports_nothing(run_import, conn):
    result = run_import([])
    assert result.exit_code == 0
    assert result.output.strip() == "Imported 0 expenses."
    assert saved(conn) == []


def test_old_ids_are_not_kept(run_import, conn):
    # new ids come from the database, so they never clash with existing rows
    ExpenseRepository(conn).add(Expense(description="Tea", amount=2, date="2026-11-01", category="Food"))
    run_import([good(id=1)])
    assert [e.id for e in saved(conn)] == [1, 2]


def test_unknown_category_becomes_other(run_import, conn):
    run_import([good(category="Pizza")])
    assert saved(conn)[0].category == "Other"


@pytest.mark.parametrize("content, message", [
    (None, "File not found"),
    ("{not json", "Not valid JSON"),
    ('{"id": 1}', "Expected a list of expenses"),
    ('["Lunch"]', "Expense 1 is not an object"),
])
def test_bad_file_imports_nothing(run_import, conn, content, message):
    result = run_import(content)
    assert result.exit_code == 1
    assert message in result.output
    assert "Nothing was imported." in result.output
    assert saved(conn) == []


@pytest.mark.parametrize("bad, message", [
    ({"description": ""}, "Please write a description"),
    ({"description": 123}, "Please write a description"),
    ({"amount": 0}, "Please enter a positive number"),
    ({"amount": "abc"}, "Amount must be a number"),
    ({"amount": True}, "Amount must be a number"),
    ({"amount": None}, "Amount must be a number"),
    ({"date": "2026-02-30"}, "Please enter a valid date"),
    ({"date": 20261105}, "Please enter a valid date"),
])
def test_one_bad_expense_imports_nothing(run_import, conn, bad, message):
    # the third expense is broken, so the two good ones are not saved either
    result = run_import([good(), good(), good(**bad)])
    assert result.exit_code == 1
    assert f"Expense 3: {message}" in result.output
    assert saved(conn) == []


def test_not_utf8_file_imports_nothing(app, tmp_path, conn):
    path = tmp_path / "expenses.json"
    path.write_bytes(b"\xff\xfe\x00")
    result = app.test_cli_runner().invoke(args=["import-json", str(path)])
    assert result.exit_code == 1
    assert "Not valid JSON" in result.output
    assert saved(conn) == []
