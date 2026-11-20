import json


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
