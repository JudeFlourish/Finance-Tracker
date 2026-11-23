import sqlite3

import pytest

from finance_tracker import create_app
from finance_tracker.expenses.models import Expense
from finance_tracker.expenses.repository import ExpenseRepository
from finance_tracker.income.models import Income
from finance_tracker.income.repository import IncomeRepository
from finance_tracker.income.validation import validate_income
from finance_tracker.models import Entry, total
from finance_tracker.validation import ValidationError


def make(source="Salary", amount=1500, date="2026-11-01"):
    return Income(source=source, amount=amount, date=date)


@pytest.fixture
def repo(conn):
    return IncomeRepository(conn)


@pytest.fixture
def sample(repo):
    # income in October and November
    repo.add(make("Salary", 1500, "2026-10-28"))
    repo.add(make("Freelance", 200, "2026-11-03"))
    repo.add(make("Salary", 1500, "2026-11-28"))
    return repo


def sources_and_dates(income):
    return [(i.source, i.date) for i in income]


# model

def test_income_is_an_entry():
    # so total() and the dashboard work on income like on expenses
    assert isinstance(make(), Entry)
    assert total([make(amount=1500), make(amount=200)]) == 1700


# add / get / delete

def test_add_returns_id_and_get_reads_it_back(repo):
    new_id = repo.add(make())
    assert repo.get(new_id) == Income(id=new_id, source="Salary", amount=1500, date="2026-11-01")


def test_get_unknown_id_returns_none(repo):
    assert repo.get(99) is None


def test_delete_removes_only_that_income(sample):
    first = sample.list()[-1]
    assert sample.delete(first.id) is True
    assert sources_and_dates(sample.list()) == [("Salary", "2026-11-28"), ("Freelance", "2026-11-03")]


def test_delete_unknown_id_returns_false(repo):
    assert repo.delete(99) is False


def test_income_is_kept_apart_from_expenses(conn, repo):
    repo.add(make())
    assert ExpenseRepository(conn).list() == []
    ExpenseRepository(conn).add(Expense(description="Lunch", amount=12.5, date="2026-11-01", category="Food"))
    assert [i.source for i in repo.list()] == ["Salary"]


# list

def test_list_newest_first(sample):
    assert sources_and_dates(sample.list()) == [
        ("Salary", "2026-11-28"), ("Freelance", "2026-11-03"), ("Salary", "2026-10-28"),
    ]


def test_same_day_keeps_a_fixed_order(repo):
    repo.add(make("First", date="2026-11-05"))
    repo.add(make("Second", date="2026-11-05"))
    assert [i.source for i in repo.list()] == ["Second", "First"]


@pytest.mark.parametrize("start, end, expected", [
    ("2026-11-01", "2026-11-30", [("Salary", "2026-11-28"), ("Freelance", "2026-11-03")]),
    ("2026-10-01", "2026-10-31", [("Salary", "2026-10-28")]),
    ("2026-11-03", "", [("Salary", "2026-11-28"), ("Freelance", "2026-11-03")]),
    ("", "2026-11-03", [("Freelance", "2026-11-03"), ("Salary", "2026-10-28")]),
    ("2026-12-01", "2026-12-31", []),
])
def test_list_by_date_range(sample, start, end, expected):
    assert sources_and_dates(sample.list(start, end)) == expected


# database rules, even if validation is skipped

@pytest.mark.parametrize("fields", [
    {"amount": 0},
    {"amount": -1},
    {"source": "   "},
    {"date": "01/11/2026"},
])
def test_database_rejects_bad_rows(repo, fields):
    income = make()
    for name, value in fields.items():
        setattr(income, name, value)
    with pytest.raises(sqlite3.IntegrityError):
        repo.add(income)
    assert repo.list() == []


def test_existing_database_gets_income_table_on_start(tmp_path):
    # a database made before income existed: only the expenses table, with data
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
    assert "income" in tables
    assert conn.execute("SELECT description FROM expenses").fetchall() == [("Lunch",)]
    conn.close()


# validate_income

def test_validate_income():
    assert validate_income({"source": " Salary ", "amount": "1500", "date": "2026-11-01"}) == Income(
        source="Salary", amount=1500.0, date="2026-11-01",
    )


@pytest.mark.parametrize("form, message", [
    ({"source": "", "amount": "1500"}, "Please write where the income came from"),
    ({"source": "   ", "amount": "1500"}, "Please write where the income came from"),
    ({"source": "Salary", "amount": "abc"}, "Amount must be a number"),
    ({"source": "Salary", "amount": "0"}, "Please enter a positive number"),
    ({"source": "Salary", "amount": "1500", "date": "2026-02-30"}, "Please enter a valid date"),
])
def test_validate_income_rejects_bad_forms(form, message):
    with pytest.raises(ValidationError, match=message):
        validate_income(form)


# /income page

def messages(client):
    # what the next page will show as flash messages
    with client.session_transaction() as session:
        return [message for _, message in session.get("_flashes", [])]


@pytest.fixture
def add_income(client):
    """Post the add-income form; any field can be overridden."""
    def _add(**fields):
        form = {"source": "Salary", "amount": "1500", "date": "2026-11-01"}
        form.update(fields)
        return client.post("/income/", data=form)
    return _add


def test_page_empty(client):
    response = client.get("/income/")
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "<h1>Income</h1>" in page
    assert "No income yet" in page
    assert "$0.00" in page


def test_page_lists_income_newest_first_with_total(client, sample):
    page = client.get("/income/").get_data(as_text=True)
    assert page.index("2026-11-28") < page.index("2026-11-03") < page.index("2026-10-28")
    assert "<td>Freelance</td>" in page
    assert "$3200.00" in page


def test_add_income(client, repo, add_income):
    response = add_income(source=" Salary ", amount="1500", date="2026-11-01")
    assert response.status_code == 302
    assert response.location == "/income/"
    assert messages(client) == ["Income added."]
    [saved] = repo.list()
    assert saved == Income(id=saved.id, source="Salary", amount=1500.0, date="2026-11-01")


@pytest.mark.parametrize("fields, message", [
    ({"source": "  "}, "Please write where the income came from"),
    ({"amount": "abc"}, "Amount must be a number"),
    ({"amount": "-5"}, "Please enter a positive number"),
    ({"date": "2026-02-30"}, "Please enter a valid date"),
])
def test_add_rejects_invalid_input(client, repo, add_income, fields, message):
    response = add_income(**fields)
    assert response.status_code == 302
    assert messages(client) == [message]
    assert repo.list() == []


def test_add_goes_back_to_next_page(add_income):
    # the dashboard's quick add will send next="/"
    assert add_income(next="/").location == "/"
    assert add_income(next="//evil.com").location == "/income/"


def test_delete_income(client, repo, add_income):
    add_income()
    [saved] = repo.list()
    response = client.post(f"/income/{saved.id}/delete")
    assert response.status_code == 302
    assert messages(client)[-1] == "Income deleted."
    assert repo.list() == []


def test_delete_unknown_income_returns_404(client):
    response = client.post("/income/99/delete")
    assert response.status_code == 404
    assert "Page not found" in response.get_data(as_text=True)


def test_delete_asks_first(client, add_income):
    add_income()
    page = client.get("/income/").get_data(as_text=True)
    assert 'data-confirm="Delete this income?"' in page


def test_income_not_counted_on_expenses_page(client, add_income, add_expense):
    add_income(source="Salary", amount="1500")
    add_expense(description="Lunch", amount="12.50", category="Food")
    page = client.get("/expenses/").get_data(as_text=True)
    assert "Salary" not in page
    assert "$12.50" in page
    assert "1500" not in page  # not in the list, total or chart data
