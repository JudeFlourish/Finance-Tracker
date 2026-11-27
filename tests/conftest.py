import pytest

from flask_migrate import upgrade

from finance_tracker import create_app
from finance_tracker.database import db


@pytest.fixture
def app(tmp_path):
    # every test gets its own empty database, so the real one is never touched
    app = create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "test.db"),
    })
    # the real migrations, so tests use exactly the tables everyone else gets
    with app.app_context():
        upgrade()
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def app_context(app):
    # one app context for the whole test, shared by session and client requests
    with app.app_context():
        yield


@pytest.fixture
def session(app_context):
    """The SQLAlchemy session that the repositories use."""
    return db.session


@pytest.fixture
def add_expense(client):
    """Post the add-expense form; any field can be overridden."""
    def _add(**fields):
        form = {"description": "Lunch", "amount": "12.50", "date": "2026-11-05", "category": "Food"}
        form.update(fields)
        return client.post("/expenses/add", data=form)
    return _add
