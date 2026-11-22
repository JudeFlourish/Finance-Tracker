import pytest

from finance_tracker import create_app
from finance_tracker.db import get_db


@pytest.fixture
def app(tmp_path):
    # every test gets its own empty database, so the real one is never touched
    return create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "test.db"),
    })


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def conn(app):
    with app.app_context():
        yield get_db()


@pytest.fixture
def add_expense(client):
    """Post the add-expense form; any field can be overridden."""
    def _add(**fields):
        form = {"description": "Lunch", "amount": "12.50", "date": "2026-11-05", "category": "Food"}
        form.update(fields)
        return client.post("/add", data=form)
    return _add
