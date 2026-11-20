import json
import os


def write_expenses(app, expenses):
    with open(app.config["DATA_FILE"], "w") as f:
        json.dump(expenses, f)


def read_expenses(app):
    with open(app.config["DATA_FILE"], "r") as f:
        return json.load(f)


def test_edit_button_and_update_route(app, client):
    write_expenses(app, [
        {
            "id": 1,
            "description": "Groceries",
            "amount": 25.5,
            "date": "2026-10-01",
            "category": "Food",
        }
    ])

    response = client.get("/")
    assert response.status_code == 200
    assert b"Edit" in response.data

    response = client.post(
        "/update/1",
        data={
            "description": "Groceries Updated",
            "amount": "30.75",
            "date": "2026-10-02",
            "category": "Food",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302

    expenses = read_expenses(app)
    assert expenses[0]["description"] == "Groceries Updated"
    assert expenses[0]["amount"] == 30.75
    assert expenses[0]["date"] == "2026-10-02"


def test_add_saves_valid_expense(app, client):
    response = client.post("/add", data={
        "description": " Bus ", "amount": "3", "date": "2026-11-05", "category": "Pizza",
    })
    assert response.status_code == 302
    assert read_expenses(app) == [
        {"id": 1, "description": "Bus", "amount": 3.0, "date": "2026-11-05", "category": "Other"},
    ]


def test_add_rejects_invalid_date(app, client):
    response = client.post("/add", data={
        "description": "Bus", "amount": "3", "date": "2026-02-30", "category": "Transport",
    })
    assert "error=Please+enter+a+valid+date" in response.location
    # nothing was saved, so the data file was never created
    assert not os.path.exists(app.config["DATA_FILE"])
