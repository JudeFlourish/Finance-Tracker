import json

from financeapp import app, DATA_FILE


def setup_module(module):
    with open(DATA_FILE, "w") as f:
        json.dump([
            {
                "id": 1,
                "description": "Groceries",
                "amount": 25.5,
                "date": "2026-10-01",
                "category": "Food",
            }
        ], f)


def test_edit_button_and_update_route():
    client = app.test_client()

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

    with open(DATA_FILE, "r") as f:
        expenses = json.load(f)

    assert expenses[0]["description"] == "Groceries Updated"
    assert expenses[0]["amount"] == 30.75
    assert expenses[0]["date"] == "2026-10-02"
