import pytest
from flask.testing import FlaskClient
from flask_migrate import upgrade

from finance_tracker import create_app
from finance_tracker.database import db


class Client(FlaskClient):
    """Every request gets its own app context, like in the real app.

    Without this, a request made while a test holds an app context open (the
    session fixture) would reuse that context and its `g`, where Flask-Login
    keeps the logged-in user. Then one client would look logged in as another.
    """

    def open(self, *args, **kwargs):
        with self.application.app_context():
            return super().open(*args, **kwargs)


@pytest.fixture
def app(tmp_path):
    # every test gets its own empty database, so the real one is never touched
    app = create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "test.db"),
    })
    app.test_client_class = Client
    # the real migrations, so tests use exactly the tables everyone else gets
    with app.app_context():
        upgrade()
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def app_context(app):
    # one app context for the test's own database work (requests get their own, see Client)
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
