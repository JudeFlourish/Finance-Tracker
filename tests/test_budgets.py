import pytest
from sqlalchemy.exc import IntegrityError

from finance_tracker.budgets.models import Budget
from finance_tracker.budgets.repository import BudgetRepository
from finance_tracker.budgets.validation import validate_budget
from finance_tracker.expenses.models import Expense
from finance_tracker.expenses.repository import ExpenseRepository
from finance_tracker.validation import ValidationError


@pytest.fixture
def repo(session):
    return BudgetRepository(session)


# create, change, delete

def test_save_creates_budget(repo):
    repo.save(Budget(category="Food", monthly_limit=300))
    budget = repo.get_by_category("Food")
    assert budget.to_dict() == {"id": budget.id, "category": "Food", "monthly_limit": 300}


def test_get_by_category_without_budget_returns_none(repo):
    assert repo.get_by_category("Rent") is None


def test_save_again_changes_the_limit(repo):
    repo.save(Budget(category="Food", monthly_limit=300))
    first = repo.get_by_category("Food")
    repo.save(Budget(category="Food", monthly_limit=250.5))
    assert [b.to_dict() for b in repo.list()] == [{"id": first.id, "category": "Food", "monthly_limit": 250.5}]


def test_delete_removes_budget(repo):
    repo.save(Budget(category="Food", monthly_limit=300))
    repo.save(Budget(category="Rent", monthly_limit=700))
    assert repo.delete(repo.get_by_category("Food").id) is True
    assert [b.category for b in repo.list()] == ["Rent"]


def test_delete_unknown_id_returns_false(repo):
    assert repo.delete(99) is False


def test_delete_budget_keeps_expenses(session, repo):
    expenses = ExpenseRepository(session)
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
    with pytest.raises(IntegrityError):
        repo.save(Budget(category="Food", monthly_limit=limit))
    assert repo.list() == []


def test_failed_change_keeps_the_old_limit_and_the_session_works(repo):
    repo.save(Budget(category="Food", monthly_limit=300))
    with pytest.raises(IntegrityError):
        repo.save(Budget(category="Food", monthly_limit=-1))
    assert repo.get_by_category("Food").monthly_limit == 300
    repo.save(Budget(category="Rent", monthly_limit=700))
    assert [b.category for b in repo.list()] == ["Food", "Rent"]


def test_database_allows_one_budget_per_category(session):
    # add() skips save()'s "change it if it exists", so only the UNIQUE rule can stop it
    session.add(Budget(category="Food", monthly_limit=100))
    session.commit()
    session.add(Budget(category="Food", monthly_limit=200))
    with pytest.raises(IntegrityError):
        session.commit()



# validate_budget

def test_validate_budget():
    budget = validate_budget({"category": "Food", "monthly_limit": "300"})
    assert budget.to_dict() == {"id": None, "category": "Food", "monthly_limit": 300.0}


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


# /budgets page

def messages(client):
    # what the next page will show as flash messages
    with client.session_transaction() as session:
        return [message for _, message in session.get("_flashes", [])]


def test_page_lists_every_category(client):
    page = client.get("/budgets/").get_data(as_text=True)
    assert "<h1>Budgets</h1>" in page
    for category in ["Food", "Transport", "Rent", "Other"]:
        assert f'name="category" value="{category}"' in page
    assert page.count(">Set</button>") == 9
    assert ">Remove</button>" not in page


def test_nav_has_budgets_link(client):
    page = client.get("/expenses/").get_data(as_text=True)
    assert 'href="/budgets/"' in page


def test_set_budget(client, repo):
    response = client.post("/budgets/", data={"category": "Food", "monthly_limit": "300"})
    assert response.status_code == 302
    assert response.location == "/budgets/"
    assert messages(client) == ["Food budget set to $300.00 a month."]
    assert repo.get_by_category("Food").monthly_limit == 300


def test_page_shows_saved_budget(client, repo):
    repo.save(Budget(category="Food", monthly_limit=300))
    page = client.get("/budgets/").get_data(as_text=True)
    assert 'value="300.00"' in page
    assert page.count(">Update</button>") == 1
    assert page.count(">Remove</button>") == 1
    assert 'data-confirm="Remove the Food budget?"' in page


def test_change_budget_keeps_one_row(client, repo):
    client.post("/budgets/", data={"category": "Food", "monthly_limit": "300"})
    client.post("/budgets/", data={"category": "Food", "monthly_limit": "250.50"})
    assert messages(client)[-1] == "Food budget updated to $250.50 a month."
    assert [(b.category, b.monthly_limit) for b in repo.list()] == [("Food", 250.5)]


@pytest.mark.parametrize("form, message", [
    ({"category": "Food", "monthly_limit": "0"}, "Please enter a positive number"),
    ({"category": "Food", "monthly_limit": "-5"}, "Please enter a positive number"),
    ({"category": "Food", "monthly_limit": "abc"}, "Budget must be a number"),
    ({"category": "Pizza", "monthly_limit": "300"}, "Please choose a category"),
])
def test_invalid_budget_is_not_saved(client, repo, form, message):
    response = client.post("/budgets/", data=form)
    assert response.status_code == 302
    assert messages(client) == [message]
    assert repo.list() == []


def test_invalid_change_keeps_old_limit(client, repo):
    repo.save(Budget(category="Food", monthly_limit=300))
    client.post("/budgets/", data={"category": "Food", "monthly_limit": "-1"})
    assert repo.get_by_category("Food").monthly_limit == 300


def test_remove_budget_keeps_expenses(client, session, repo, add_expense):
    add_expense(description="Lunch", category="Food")
    repo.save(Budget(category="Food", monthly_limit=300))
    response = client.post(f"/budgets/{repo.get_by_category('Food').id}/delete")
    assert response.status_code == 302
    assert messages(client)[-1] == "Budget removed."
    assert repo.list() == []
    assert [e.description for e in ExpenseRepository(session).list()] == ["Lunch"]


def test_remove_unknown_budget_returns_404(client):
    assert client.post("/budgets/99/delete").status_code == 404


def test_budget_page_does_not_load_chart_script(client):
    # script.js needs Chart.js, which only the expenses page loads
    page = client.get("/budgets/").get_data(as_text=True)
    assert "script.js" not in page
    assert "confirm.js" in page
