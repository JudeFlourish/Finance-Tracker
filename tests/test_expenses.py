import pytest

from finance_tracker.expenses.charts import chart_data
from finance_tracker.expenses.models import Expense
from finance_tracker.expenses.repository import ExpenseRepository


@pytest.fixture
def repo(conn):
    return ExpenseRepository(conn)


def messages(client):
    # what the next page will show as flash messages
    with client.session_transaction() as session:
        return [message for _, message in session.get("_flashes", [])]


# home page

def test_home_page_lists_expenses_and_total(client, add_expense):
    add_expense(description="Lunch", amount="12.50")
    add_expense(description="Bus", amount="3")
    page = client.get("/expenses/").get_data(as_text=True)
    assert "<td>Lunch</td>" in page and "<td>Bus</td>" in page
    assert "$15.50" in page


def test_home_page_empty(client):
    page = client.get("/expenses/").get_data(as_text=True)
    assert "No expenses yet" in page


def test_home_page_escapes_user_input(client, add_expense):
    add_expense(description="<script>alert(1)</script>")
    page = client.get("/expenses/").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;" in page


# add

def test_add_saves_expense(client, add_expense, repo):
    response = add_expense(description=" Bus ", amount="3", date="2026-11-05", category="Pizza")
    assert response.status_code == 302
    assert messages(client) == ["Expense added."]
    [saved] = repo.list()
    assert saved == Expense(id=saved.id, description="Bus", amount=3.0, date="2026-11-05", category="Other")


@pytest.mark.parametrize("fields, message", [
    ({"description": "  "}, "Please write a description"),
    ({"amount": "abc"}, "Amount must be a number"),
    ({"amount": "-5"}, "Please enter a positive number"),
    ({"date": "2026-02-30"}, "Please enter a valid date"),
])
def test_add_rejects_invalid_input(client, add_expense, repo, fields, message):
    response = add_expense(**fields)
    assert response.status_code == 302
    assert messages(client) == [message]
    assert repo.list() == []


def test_message_is_shown_once(client, add_expense):
    add_expense()
    assert "Expense added." in client.get("/expenses/").get_data(as_text=True)
    assert "Expense added." not in client.get("/expenses/").get_data(as_text=True)


# edit / update

def test_edit_page_is_prefilled(client, repo):
    new_id = repo.add(Expense(description="Groceries", amount=25.5, date="2026-10-01", category="Food"))
    page = client.get(f"/expenses/edit/{new_id}").get_data(as_text=True)
    assert "Edit Expense" in page
    assert 'value="Groceries"' in page
    assert 'value="25.5"' in page
    assert 'value="2026-10-01"' in page


def test_update_saves_changes(client, repo):
    new_id = repo.add(Expense(description="Groceries", amount=25.5, date="2026-10-01", category="Food"))
    response = client.post(f"/expenses/update/{new_id}", data={
        "description": "Groceries Updated", "amount": "30.75", "date": "2026-10-02", "category": "Health",
    })
    assert response.status_code == 302
    assert messages(client) == ["Expense updated."]
    assert repo.get(new_id) == Expense(
        id=new_id, description="Groceries Updated", amount=30.75, date="2026-10-02", category="Health",
    )


def test_update_invalid_goes_back_to_edit_form(client, repo):
    new_id = repo.add(Expense(description="Groceries", amount=25.5, date="2026-10-01", category="Food"))
    response = client.post(f"/expenses/update/{new_id}", data={
        "description": "Groceries", "amount": "0", "next": "/expenses/?category=Food",
    })
    assert response.location.startswith(f"/expenses/edit/{new_id}")
    assert "next=" in response.location
    assert messages(client) == ["Please enter a positive number"]
    assert repo.get(new_id).amount == 25.5


# delete

def test_delete_removes_expense(client, add_expense, repo):
    add_expense()
    [saved] = repo.list()
    response = client.post(f"/expenses/delete/{saved.id}")
    assert response.status_code == 302
    assert messages(client)[-1] == "Expense deleted."
    assert repo.list() == []


# unknown ids

@pytest.mark.parametrize("method, url", [
    ("get", "/expenses/edit/99"),
    ("post", "/expenses/update/99"),
    ("post", "/expenses/delete/99"),
])
def test_unknown_id_returns_404(client, method, url):
    response = getattr(client, method)(url, data={"description": "X", "amount": "1"})
    assert response.status_code == 404


# going back to the same filtered page

def test_add_returns_to_filtered_page(add_expense):
    response = add_expense(next="/expenses/?category=Food")
    assert response.location == "/expenses/?category=Food"


def test_delete_returns_to_filtered_page(client, add_expense, repo):
    add_expense()
    [saved] = repo.list()
    response = client.post(f"/expenses/delete/{saved.id}", data={"next": "/expenses/?start=2026-11-01"})
    assert response.location == "/expenses/?start=2026-11-01"


def test_update_returns_to_filtered_page(client, add_expense, repo):
    add_expense()
    [saved] = repo.list()
    response = client.post(f"/expenses/update/{saved.id}", data={
        "description": "Lunch", "amount": "5", "next": "/expenses/?category=Food",
    })
    assert response.location == "/expenses/?category=Food"


def test_next_to_another_site_is_ignored(add_expense):
    response = add_expense(next="//evil.com")
    assert response.location == "/expenses/"


def test_forms_carry_the_current_filter(client, add_expense):
    add_expense()
    page = client.get("/expenses/?category=Food").get_data(as_text=True)
    assert 'name="next" value="/expenses/?category=Food"' in page


def test_edit_cancel_goes_back_to_filtered_page(client, add_expense, repo):
    add_expense()
    [saved] = repo.list()
    page = client.get(f"/expenses/edit/{saved.id}?next=/expenses/%3Fcategory%3DFood").get_data(as_text=True)
    assert 'href="/expenses/?category=Food"' in page


def test_edit_ignores_unsafe_next(client, add_expense, repo):
    add_expense()
    [saved] = repo.list()
    page = client.get(f"/expenses/edit/{saved.id}?next=//evil.com").get_data(as_text=True)
    assert "evil.com" not in page


# filter and export

@pytest.fixture
def three_expenses(add_expense):
    add_expense(description="Lunch", amount="12.50", date="2026-11-01", category="Food")
    add_expense(description="Bus", amount="3", date="2026-11-05", category="Transport")
    add_expense(description="Dinner", amount="20", date="2026-11-10", category="Food")


def test_filter_by_category(client, three_expenses):
    page = client.get("/expenses/?category=Food").get_data(as_text=True)
    assert "<td>Lunch</td>" in page and "<td>Dinner</td>" in page
    assert "<td>Bus</td>" not in page
    assert "$32.50" in page


def test_filter_by_date_range(client, three_expenses):
    page = client.get("/expenses/?start=2026-11-02&end=2026-11-09").get_data(as_text=True)
    assert "<td>Bus</td>" in page
    assert "<td>Lunch</td>" not in page and "<td>Dinner</td>" not in page


def test_bad_filter_values_are_ignored(client, three_expenses):
    response = client.get("/expenses/?start=2026-02-30&category=Pizza")
    assert response.status_code == 200
    assert "$35.50" in response.get_data(as_text=True)


def test_export_matches_filter_oldest_first(client, three_expenses):
    response = client.get("/expenses/export?category=Food")
    assert response.mimetype == "text/csv"
    assert "attachment; filename=expenses.csv" in response.headers["Content-Disposition"]
    assert response.get_data(as_text=True).splitlines() == [
        "Date,Description,Category,Amount",
        "2026-11-01,Lunch,Food,12.50",
        "2026-11-10,Dinner,Food,20.00",
    ]


# chart data

def test_chart_data():
    expenses = [
        Expense(description="Lunch", amount=12.5, date="2026-11-01", category="Food"),
        Expense(description="Bus", amount=3, date="2026-11-01", category="Transport"),
        Expense(description="Dinner", amount=20, date="2026-11-10", category="Food"),
    ]
    assert chart_data(expenses) == {
        "pie_labels": ["Food", "Transport"],
        "pie_values": [32.5, 3],
        "pie_colors": ["#36a2eb", "#ff6384"],
        "bar_labels": ["2026-11-01", "2026-11-10"],
        "bar_values": [15.5, 20],
    }


def test_chart_data_empty():
    assert chart_data([]) == {
        "pie_labels": [], "pie_values": [], "pie_colors": [], "bar_labels": [], "bar_values": [],
    }
