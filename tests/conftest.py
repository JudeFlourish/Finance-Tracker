import pytest

from finance_tracker import create_app
from finance_tracker.db import get_db


@pytest.fixture
def app(tmp_path):
    # every test gets its own database and data file,
    # so the real instance/finance.db and expenses.json are never touched
    return create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "test.db"),
        "DATA_FILE": str(tmp_path / "expenses.json"),
    })


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def conn(app):
    with app.app_context():
        yield get_db()
